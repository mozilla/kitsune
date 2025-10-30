from django.core.management.base import BaseCommand

from kitsune.sumo.utils import CommandLogger
from kitsune.users.tasks import cleanup_expired_users


class Command(BaseCommand):
    help = "Delete users who haven't logged in for more than settings.USER_INACTIVITY_DAYS days"

    def handle(self, *args, **options):
        cleanup_expired_users(logger=CommandLogger(self, options))
