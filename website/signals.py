from django.utils import timezone
from django.core.cache import cache


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