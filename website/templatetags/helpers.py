from django import template
from django.core.cache import cache

from website.helpers import prettify, make_cache_key
from django.conf import settings
import os.path

register = template.Library()


def get_category_image(category):
    cache_key = make_cache_key('category_image', category)
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    base_path = settings.BASE_DIR + '/static/website/images/'
    file_name = category.replace(' ', '-') + '.jpg'
    file_path = base_path + file_name
    if os.path.isfile(file_path):
        value = 'website/images/' + file_name
    else:
        value = False

    cache.set(cache_key, value, 3600)
    return value


register.filter('get_category_image', get_category_image)
# imported from website/helpers
register.simple_tag(prettify)
