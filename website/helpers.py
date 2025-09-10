import re
import json
import logging
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from website.models import Question, User
from nltk.corpus import stopwords
from website.templatetags.permission_tags import can_edit, can_hide_delete
from sklearn.metrics.pairwise import cosine_similarity
from django.conf import settings
from django.utils import timezone
from django.db.models import Q
import re
from .models import SpamRule, SpamLog   # assuming app is `forum`

sw = stopwords.words('english')

# Configure logging for spam detection
logging.basicConfig(level=logging.INFO)
spam_logger = logging.getLogger('spam_detection')


def get_video_info(path):
    """Uses ffmpeg to determine information about a video. This has not been broadly
    tested and your milage may vary"""

    from decimal import Decimal
    import subprocess
    import re

    process = subprocess.Popen(['/usr/bin/ffmpeg', '-i', path], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    stdout, stderr = process.communicate()
    duration_m = re.search(r"Duration:\s{1}(?P<hours>\d+?):(?P<minutes>\d+?):(?P<seconds>\d+\.\d+?)", stdout.decode("UTF-8"), re.DOTALL).groupdict()
    info_m = re.search(r": Video: (?P<codec>.*?), (?P<profile>.*?), (?P<width>.*?)x(?P<height>.*?), ", stdout.decode("UTF-8"), re.DOTALL).groupdict()
    hours = Decimal(duration_m['hours'])
    minutes = Decimal(duration_m['minutes'])
    seconds = Decimal(duration_m['seconds'])

    total = 0
    total += 60 * 60 * hours
    total += 60 * minutes
    total += seconds

    info_m['hours'] = hours
    info_m['minutes'] = minutes
    info_m['seconds'] = seconds
    info_m['duration'] = total
    return info_m


def prettify(string):
    string = string.lower()
    string = string.replace('-', ' ')
    string = string.strip()
    string = string.replace(' ', '-')
    string = re.sub('[^A-Za-z0-9\-]+', '', string)
    string = re.sub('-+', '-', string)
    return string


def pre_process(text):
    text=text.lower()                       # lowercase
    text=re.sub("<!--?.*?-->","",text)      # remove tags
    text=re.sub("(\\d|\\W)+"," ",text)      # remove special characters and digits
    return text

def clean_user_data(text):
    from nltk.tokenize import word_tokenize
    words = word_tokenize(pre_process(text.lower()))
    clean_list = [w for w in words if not w in sw]
    return clean_list

def get_similar_questions(user_ques,question):
    from nltk.tokenize import word_tokenize
    total = []
    l1 = []
    l2 = []
    question = word_tokenize(pre_process(question))
    question =[w for w in question if not w in sw]
    total = user_ques + question
    for w in total: 
        if w in user_ques: l1.append(1) # create a vector 
        else: l1.append(0) 
        if w in question: l2.append(1) 
        else: l2.append(0)        
    cs = cosine_similarity((l1,l2))
    return cs[0][1]


# helpers.py

MULTIPLE_URL_WEIGHT = 20
MULTIPLE_URL_THRESHOLD = 3

class SpamQuestionDetector:
    def __init__(self):
        # load only active + not expired rules
        now = timezone.now()
        qs = SpamRule.objects.filter(active=True).filter(
            Q(expires_at__isnull=True) | Q(expires_at__gt=now)
        )
        self._compiled = []
        for r in qs:
            try:
                cre = re.compile(r.pattern, re.IGNORECASE)
            except re.error:
                spam_logger.warning(f"Invalid regex in SpamRule id={r.id}: {r.pattern}")
                continue
            self._compiled.append({
                'rule': r,
                'compiled': cre
            })

    def extract_urls(self, text: str):
        return re.findall(r'https?://[^\s)<>"]+', text)

    def detect_spam(self, title: str, content: str, category: str = "", tutorial: str = "") -> dict:
        combined_text = " ".join(filter(None, [title, content, category, tutorial])).lower()
        spam_score = 0
        matches = []

        for entry in self._compiled:
            rule = entry['rule']
            cre = entry['compiled']
            if cre.search(combined_text):
                spam_score += rule.score
                matches.append({
                    'id': rule.id,
                    'pattern': rule.pattern,
                    'score': rule.score,
                    'type': rule.type,
                    'notes': rule.notes
                })

        # detect multiple URLs (we keep this behaviour from original)
        urls = self.extract_urls(combined_text)
        if len(urls) >= MULTIPLE_URL_THRESHOLD:
            spam_score += MULTIPLE_URL_WEIGHT
            matches.append({
                'pattern': f'{len(urls)} URLs',
                'score': MULTIPLE_URL_WEIGHT,
                'type': 'urls'
            })

        # classification (same thresholds as earlier)
        if spam_score >= 60:
            confidence, action = 'HIGH', 'DELETE'
        elif spam_score >= 30:
            confidence, action = 'MEDIUM', 'REVIEW'
        elif spam_score >= 15:
            confidence, action = 'LOW', 'REVIEW'
        else:
            confidence, action = 'CLEAN', 'APPROVE'

        result = {
            'spam_score': spam_score,
            'matches': matches,
            'confidence': confidence,
            'recommended_action': action,
            'url_count': len(urls)
        }

        # debug log
        spam_logger.info(f"SpamDetect result: score={spam_score} action={action} matches={len(matches)}")

        return result


def handle_spam(question, user, delete_on_high=True, save_question_metadata_before_delete=True):
    """
    Runs detection on a saved Question instance and logs/takes action.
    - question: saved Question instance (has .id)
    - user: Django user instance who created the question (for logging)
    - delete_on_high: if True, HIGH confidence -> delete from DB; otherwise hide it (status=0)
    Returns a status string: 'AUTO_DELETE', 'FLAGGED', 'APPROVED', 'HIDDEN'
    """
    detector = SpamQuestionDetector()
    result = detector.detect_spam(
        title=getattr(question, 'title', '') or '',
        content=getattr(question, 'body', '') or '',
        category=getattr(question, 'category', '') or '',
        tutorial=getattr(question, 'tutorial', '') or ''
    )

    spam_score = result['spam_score']
    confidence = result['confidence']
    action = result['recommended_action']
    details = result['matches']

    # prepare log payload
    log_payload = {
        #'question_id': question.id,
        'user_id': user.id if user else None,
        'category': getattr(question, 'category', '') or '',
        'title': getattr(question, 'title', '') or '',
        'content': getattr(question, 'body', '') or '',
        'action': None,
        'spam_score': spam_score,
        'confidence': confidence,
        'details': details
    }

    # TAKE ACTION
    if action == 'DELETE' and confidence == 'HIGH':
        log_payload['action'] = 'AUTO_DELETE'
        SpamLog.objects.create(**log_payload)

        if delete_on_high:
            # delete after logging
            spam_logger.info(f"AUTO_DELETE: Question {question.id} by user {user.id} score={spam_score}")
            question.delete()
            return 'AUTO_DELETE'
        else:
            # hide instead of delete
            question.spam = True
            question.status = 0
            question.save(update_fields=['spam', 'status'])
            return 'HIDDEN'

    elif action == 'REVIEW':
        # flag for admin review
        log_payload['action'] = 'FLAGGED'
        SpamLog.objects.create(**log_payload)

        question.approval_required = True
        question.spam = False
        question.save(update_fields=['approval_required', 'spam'])
        return 'FLAGGED'

    else:
        # APPROVE / CLEAN
        question.spam = False
        question.approval_required = False
        question.save(update_fields=['spam', 'approval_required'])
        return 'APPROVED'