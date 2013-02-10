from django.contrib.auth.models import User
from django.contrib.auth.hashers import UNUSABLE_PASSWORD


def run():
    users = User.objects.filter(password='PASSWORD_DISABLED')
    num = users.update(password=UNUSABLE_PASSWORD)
    if not num:
        print 'There is nothing to update.'
        return
    print 'Done! Updated %d passwords.' % num
