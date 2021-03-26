def is_administrator(user):
    if user and user.groups.filter(name='Administrator').count() == 1:
        return True

def is_forumsadmin(user):
    if user and user.groups.filter(name='Forums-Admin').count() == 1:
        return True