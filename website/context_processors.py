from django.conf import settings


def booleans():
    return {
        'True': True,
        'False': False,
    }


def spoken_urls(request=None):
    if request:
        scheme = 'https' if request.is_secure() else 'http'
        host = request.get_host().split(':')[0]
        forum_url = f"{scheme}://{request.get_host()}"

        if host.startswith('forums.'):
            spoken_host = host.replace('forums.', '', 1)
            inferred_spoken_url = f"{scheme}://{spoken_host}"
            inferred_spoken_name = spoken_host
        else:
            inferred_spoken_url = None
            inferred_spoken_name = host
    else:
        forum_url = getattr(settings, 'FORUMS_URL', getattr(settings, 'FORUMS_SPOKEN_URL', 'https://forums.spoken-tutorial.org'))
        inferred_spoken_url = None
        inferred_spoken_name = 'spoken-tutorial.org'

    if inferred_spoken_url:
        spoken_url = inferred_spoken_url
    else:
        spoken_url = (
            getattr(settings, 'SPOKEN_URL', None)
            or getattr(settings, 'EDUPYRAMIDS_URL', None)
            or getattr(settings, 'SPOKEN_BASE_URL', 'https://spoken-tutorial.org')
        )

    if 'edupyramids' in spoken_url.lower():
        spoken_name = 'EduPyramids'
        spoken_domain = 'edupyramids.in'
    elif 'spoken-tutorial' in spoken_url.lower():
        spoken_name = 'Spoken-Tutorial.org'
        spoken_domain = 'spoken-tutorial.org'
    else:
        spoken_name = inferred_spoken_name
        spoken_domain = inferred_spoken_name

    return {
        'FORUMS_URL': forum_url,
        'FORUMS_SPOKEN_URL': forum_url,
        'FORUM_URL': forum_url,
        'SPOKEN_URL': spoken_url,
        'SPOKEN_BASE_URL': spoken_url,
        'EDUPYRAMIDS_URL': spoken_url,
        'MAIN_WEBSITE_URL': spoken_url,
        'SPOKEN_NAME': spoken_name,
        'SPOKEN_DOMAIN': spoken_domain,
        'PROCESS_URL': getattr(settings, 'PROCESS_URL', 'https://process.spoken-tutorial.org'),
        'IS_EDU_URL': getattr(settings, 'IS_EDU_URL', True),
    }
