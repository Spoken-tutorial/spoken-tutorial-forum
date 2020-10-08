from django.utils import timezone

def last_active_signal_from_answer(sender, instance, created, **kwargs):
    if created or not created:
        instance.question.last_active = timezone.now()
        instance.question.save()

def last_active_signal_from_reply(sender, instance, created, **kwargs):
    if created or not created:
        instance.answer.question.last_active = timezone.now()
        instance.answer.question.save()