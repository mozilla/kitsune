from datetime import datetime, timedelta

from django.core.management.base import BaseCommand
from rest_framework.authtoken.models import Token


class Command(BaseCommand):
    def handle(self, **options):
        too_old = datetime.now() - timedelta(days=30)
        Token.objects.filter(created__lt=too_old).delete()
