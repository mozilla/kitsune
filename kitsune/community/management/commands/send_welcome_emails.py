from django.core.management.base import BaseCommand

from kitsune.community.tasks import send_welcome_emails
from kitsune.sumo.utils import CommandLogger


class Command(BaseCommand):
    help = "Send a welcome email to first time contributors."

    def handle(self, **options):
        send_welcome_emails(logger=CommandLogger(self, options))
