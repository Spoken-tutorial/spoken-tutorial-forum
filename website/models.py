from django.db import models
from django.contrib.auth import get_user_model

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
