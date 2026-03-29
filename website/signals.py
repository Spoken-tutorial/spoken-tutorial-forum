import json
import logging
import threading

import requests
from django.conf import settings
from django.utils import timezone
from django.core.cache import cache

logger = logging.getLogger(__name__)


HOME_CACHE_KEYS = [
    'home:categories',
    'home:recent_questions',
    'home:active_questions',
    'home:slider_questions',
    'home:spam_questions',
    'home:category_question_map',
    'stats:total_questions',
    'stats:total_answers',
]


def clear_home_cache():
    cache.delete_many(HOME_CACHE_KEYS)


def last_active_signal_from_answer(sender, instance, created, **kwargs):
    if created or not created:
        instance.question.last_active = timezone.now()
        instance.question.last_post_by = instance.uid
        instance.question.save()
    clear_home_cache()


def last_active_signal_from_reply(sender, instance, created, **kwargs):
    if created or not created:
        instance.answer.question.last_active = timezone.now()
        instance.answer.question.last_post_by = instance.uid
        instance.answer.question.save()
    clear_home_cache()


def home_cache_invalidator(sender, instance, **kwargs):
    clear_home_cache()


# webhook helpers for social

def _send_webhook(payload):
    """Fire-and-forget POST to the Social platform's webhook endpoint.

    Runs in a daemon thread so the forum response is never delayed.
    Fails silently — the forum must keep working even if the Social app is down.
    """
    
    webhook_url = "http://localhost:8000/api/webhooks/forum" 

    if not webhook_url:
        return  

    headers = {
        'Content-Type': 'application/json',
    }

    def _post():
        try:
            resp = requests.post(
                webhook_url,
                data=json.dumps(payload),
                headers=headers,
                timeout=10,
            )
            logger.info(
                'Webhook sent: %s → %s (status %s)',
                payload.get('event'), webhook_url, resp.status_code,
            )
        except requests.RequestException as exc:
            logger.warning('Webhook delivery failed: %s', exc)

    thread = threading.Thread(target=_post, daemon=True)
    thread.start()


def _build_payload(event_type, instance, sender):
    """Build a consistent webhook payload for both Question and Answer events."""
    from .models import Question, Answer
    from django.contrib.auth import get_user_model

    User = get_user_model()
    
    
    user_email = ""
    try:
        user = User.objects.get(id=instance.uid)
        user_email = user.email
    except User.DoesNotExist:
        pass

    payload = {
        'event': event_type,
        'user_id': instance.uid,
        'email': user_email,
        'resource_id': instance.id,
        'timestamp': timezone.now().isoformat(),
    }

    if sender == Question:
        payload['category'] = instance.category
        payload['tutorial'] = instance.tutorial
        payload['title'] = instance.title
    elif sender == Answer:
        payload['question_id'] = instance.question_id
        payload['category'] = instance.question.category
        payload['tutorial'] = instance.question.tutorial

    return payload


def webhook_on_create(sender, instance, created, **kwargs):
    """Signal handler: fires when a Question or Answer is saved for the first time."""
    if not created:
        return  # We only care about new objects, not updates

    from .models import Question, Answer

    if sender == Question:
        event = 'question_created'
    elif sender == Answer:
        event = 'answer_created'
    else:
        return

    payload = _build_payload(event, instance, sender)
    _send_webhook(payload)


def webhook_on_delete(sender, instance, **kwargs):
    """Signal handler: fires when a Question or Answer is deleted."""
    from .models import Question, Answer

    if sender == Question:
        event = 'question_deleted'
    elif sender == Answer:
        event = 'answer_deleted'
    else:
        return

    payload = _build_payload(event, instance, sender)
    _send_webhook(payload)