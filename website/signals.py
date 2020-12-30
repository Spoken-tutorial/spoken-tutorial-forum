from django.utils import timezone

def last_active_signal_from_answer(sender, instance, created, **kwargs):
    if created or not created:
        instance.question.last_active = timezone.now()
        instance.question.last_post_by = instance.uid
        instance.question.save()

def last_active_signal_from_reply(sender, instance, created, **kwargs):
    if created or not created:
        instance.answer.question.last_active = timezone.now()
        instance.answer.question.last_post_by = instance.uid
        instance.answer.question.save()