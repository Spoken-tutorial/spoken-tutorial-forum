from django import template

from website.models import Question, Answer, Notification

register = template.Library()


def get_notification(nid):
    notification = Notification.objects.get(pk=nid)
    try:
        question = Question.objects.get(pk=notification.qid)
    except Question.DoesNotExist:
        question =  None
    try:
        answer = Answer.objects.get(pk=notification.aid)
    except Answer.DoesNotExist:
        answer = None
    context = {
        'notification': notification,
        'question': question,
        'answer': answer,
    }
    return context


register.inclusion_tag('website/templates/notify.html')(get_notification)


def notification_count(user_id):
    count = Notification.objects.filter(uid=user_id).count()
    return count


register.simple_tag(notification_count)

# retriving the latest post of a category


def latest_question(category):
    question = None
    category = category.replace(' ', '-')
    try:
        question = Question.objects.filter(category=category, status=1).order_by('-date_created')[0]
    except Exception:
        pass
    context = {
        'question': question
    }
    return context


register.inclusion_tag('website/templates/latest_question.html')(latest_question)
