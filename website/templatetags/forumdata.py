from django import template
from django.conf import settings
from forums.sortable import *

register = template.Library()

@register.filter
def sort_by(queryset, order):
    return queryset.filter(visible__exact=1).order_by('position')

''' includes: will include include's values '''
def reset_get_values(getValue, includes = ['page']):
    values = ''
    for k,v in list(getValue.items()):
        if k in includes:
            values += k+'='+v+'&'
    return values

''' includes: will include include's values '''
def reset_get_value(getValue, exclude_key = None):
    values = ''
    for k,v in list(getValue.items()):
        if k != exclude_key:
            if values:
                values += '&'
            values += k + '=' + v
    return values
    
register.filter('reset_get_values', reset_get_values)
register.filter('reset_get_value', reset_get_value)
register.inclusion_tag('website/templates/sortable_header.html')(get_sortable_header)