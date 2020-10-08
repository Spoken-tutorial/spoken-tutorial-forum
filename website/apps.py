from django.apps import AppConfig
from django.db.models.signals import post_save

class WebsiteConfig(AppConfig):
    name = 'website'

    def ready(self):
        from .models import Answer, AnswerComment
        from .signals import last_active_signal_from_answer, last_active_signal_from_reply
        post_save.connect(last_active_signal_from_answer, sender=Answer, dispatch_uid='trigger_last_active_answer')
        post_save.connect(last_active_signal_from_reply, sender=AnswerComment, dispatch_uid='trigger_last_active_reply')