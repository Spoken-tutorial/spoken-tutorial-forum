from django import template
from django.db.models import Count

from website.models import Question

register = template.Library()


def recent_questions():
    recent_questions = (
        Question.objects.all()
        .annotate(total_answers=Count('answer'))
        .order_by('-id')[:5]
    )
    return {
        'questions': recent_questions,
        'total': 10,
        'marker': 0,
    }


register.inclusion_tag('website/templates/recent-questions.html')(recent_questions)
