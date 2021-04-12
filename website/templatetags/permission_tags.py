from django import template

from website.permissions import is_administrator, is_forumsadmin

register = template.Library()


def can_edit(user, obj):
    if user.id == obj.uid or is_administrator(user):
        return True
    return False

def can_hide_delete(user, obj):
    if user.id == obj.uid or is_forumsadmin(user):
        return True
    return False

def isadministrator(user):
    return is_administrator(user)


register.filter(can_edit)
register.filter(isadministrator)
register.filter(can_hide_delete)
