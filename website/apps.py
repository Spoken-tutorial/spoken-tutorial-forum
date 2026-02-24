from django.apps import AppConfig
from django.db.models.signals import post_save, post_delete


class WebsiteConfig(AppConfig):
    name = 'website'

    def ready(self):
        from .models import Question, Answer, AnswerComment
        from .signals import (
            last_active_signal_from_answer,
            last_active_signal_from_reply,
            home_cache_invalidator,
        )

        post_save.connect(
            last_active_signal_from_answer,
            sender=Answer,
            dispatch_uid='trigger_last_active_answer',
        )
        post_save.connect(
            last_active_signal_from_reply,
            sender=AnswerComment,
            dispatch_uid='trigger_last_active_reply',
        )

        post_save.connect(
            home_cache_invalidator,
            sender=Question,
            dispatch_uid='home_cache_invalidator_question_save',
        )
        post_delete.connect(
            home_cache_invalidator,
            sender=Question,
            dispatch_uid='home_cache_invalidator_question_delete',
        )
        post_save.connect(
            home_cache_invalidator,
            sender=Answer,
            dispatch_uid='home_cache_invalidator_answer_save',
        )
        post_delete.connect(
            home_cache_invalidator,
            sender=Answer,
            dispatch_uid='home_cache_invalidator_answer_delete',
        )
        post_save.connect(
            home_cache_invalidator,
            sender=AnswerComment,
            dispatch_uid='home_cache_invalidator_answercomment_save',
        )
        post_delete.connect(
            home_cache_invalidator,
            sender=AnswerComment,
            dispatch_uid='home_cache_invalidator_answercomment_delete',
        )