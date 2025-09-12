from django.db import models
from django.contrib.auth import get_user_model
import json
User = get_user_model()


class Question(models.Model):
    uid = models.IntegerField()
    category = models.CharField(max_length=200)
    tutorial = models.CharField(max_length=200)
    minute_range = models.CharField(max_length=10)
    second_range = models.CharField(max_length=10)
    title = models.CharField(max_length=200)
    body = models.TextField()
    date_created = models.DateTimeField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)
    views = models.IntegerField(default=1)
    status = models.IntegerField(default=1)
    last_active = models.DateTimeField(null=True)
    last_post_by = models.IntegerField(null=True)
    spam = models.BooleanField(default=False)
    approval_required = models.BooleanField(default=False)
    approved_by = models.IntegerField(null=True)
    date_approved = models.DateTimeField(auto_now_add=True)
 
    # votes = models.IntegerField(default=0)

    def user(self):
        user = User.objects.get(id=self.uid)
        return user.username
    
    def last_post_user(self):
        user = User.objects.get(id=self.last_post_by)
        return user.username

    class Meta:
        get_latest_by = "date_created"


class QuestionVote(models.Model):
    uid = models.IntegerField()
    question = models.ForeignKey(Question, on_delete=models.CASCADE,)


class QuestionComment(models.Model):
    uid = models.IntegerField()
    question = models.ForeignKey(Question, on_delete=models.CASCADE,)
    body = models.TextField()
    date_created = models.DateTimeField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)


class Answer(models.Model):
    uid = models.IntegerField()
    question = models.ForeignKey(Question, on_delete=models.CASCADE,)
    body = models.TextField()
    date_created = models.DateTimeField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)
    # votes = models.IntegerField(default=0)

    def user(self):
        user = User.objects.get(id=self.uid)
        return user.username


class AnswerVote(models.Model):
    uid = models.IntegerField()
    answer = models.ForeignKey(Answer, on_delete=models.CASCADE,)


class AnswerComment(models.Model):
    uid = models.IntegerField()
    answer = models.ForeignKey(Answer, on_delete=models.CASCADE,)
    body = models.TextField()
    date_created = models.DateTimeField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)

    def user(self):
        user = User.objects.get(id=self.uid)
        return user.username


class Notification(models.Model):
    uid = models.IntegerField()
    pid = models.IntegerField()
    qid = models.IntegerField()
    aid = models.IntegerField(default=0)
    cid = models.IntegerField(default=0)
    date_created = models.DateTimeField(auto_now_add=True)

    def poster(self):
        user = User.objects.get(id=self.pid)
        return user.username

# CDEEP database created using inspectdb arg of manage.py
class SpamRule(models.Model):
    KEYWORD = "keyword"
    DOMAIN = "domain"
    TYPES = [(KEYWORD, "Keyword"), (DOMAIN, "Domain / URL")]

    type = models.CharField(max_length=10, choices=TYPES)
    pattern = models.CharField(max_length=500)
    score = models.IntegerField(default=1)
    active = models.BooleanField(default=True)
    notes = models.CharField(max_length=200, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.type}: {self.pattern} ({self.score})"

class SpamLog(models.Model):
    ACTIONS = [
        ("AUTO_DELETE", "Auto Deleted"),
        ("FLAGGED", "Flagged for Review"),
        ("APPROVED", "Approved"),
    ]

    question_id = models.IntegerField()
    user_id = models.IntegerField(null=True, blank=True)
    category = models.CharField(max_length=200, blank=True)
    title = models.CharField(max_length=200, blank=True)
    content = models.TextField(blank=True)
    action = models.CharField(max_length=20, choices=ACTIONS)
    spam_score = models.IntegerField()
    confidence = models.CharField(max_length=20)
    details = models.TextField(blank=True, null=True)

    def set_details(self, data):
        self.details = json.dumps(data)

    def get_details(self):
        try:
            return json.loads(self.details)
        except Exception:
            return {}
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Q{self.question_id} - {self.action} ({self.spam_score})"
