from datetime import datetime, timedelta

from django.contrib.auth.models import User
from django.contrib.auth.hashers import UNUSABLE_PASSWORD_PREFIX
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Purge old hashed passwords.'

    def handle(self, *args, **kw):
        old = datetime.now() - timedelta(365)
        users = User.objects.filter(last_login__lt=old)
        users = users.exclude(password__startswith=UNUSABLE_PASSWORD_PREFIX)
        for user in users:
            user.set_unusable_password()
            user.save()

        print 'Cleared %d passwords.' % len(users)
