from datetime import datetime, timedelta

from django.contrib.auth.models import User
from django.contrib.auth.hashers import UNUSABLE_PASSWORD
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Purge old hashed passwords.'

    def handle(self, *args, **kw):
        old = datetime.now() - timedelta(365)
        users = User.objects.filter(last_login__lt=old)
        users = users.exclude(password=UNUSABLE_PASSWORD)
        num = users.update(password=UNUSABLE_PASSWORD)
        print 'Cleared %d passwords.' % num
