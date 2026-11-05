from django.conf import settings


def booleans():
    return {
        'True': True,
        'False': False,
    }


def spoken_urls(request=None):
    return {
        'PROCESS_URL': getattr(settings, 'PROCESS_URL', 'https://process.spoken-tutorial.org'),
        'FORUMS_SPOKEN_URL': getattr(settings, 'FORUMS_SPOKEN_URL', 'https://forums.spoken-tutorial.org'),
        'FORUMS_URL': getattr(settings, 'FORUMS_URL', 'https://forums.spoken-tutorial.org'),
        'SPOKEN_BASE_URL': getattr(settings, 'SPOKEN_BASE_URL', 'https://spoken-tutorial.org'),
        'EDUPYRAMIDS_URL': getattr(settings, 'EDUPYRAMIDS_URL', 'https://spoken-tutorial.org'),
        'IS_EDU_URL': getattr(settings, 'IS_EDU_URL', True),
        'SPOKEN_URL': getattr(settings, 'SPOKEN_URL', 'https://spoken-tutorial.org'),
    }
