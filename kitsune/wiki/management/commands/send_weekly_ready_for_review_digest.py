from django.core.management.base import BaseCommand

from kitsune.wiki.tasks import send_weekly_ready_for_review_digest


class Command(BaseCommand):
    help = 'Sends out the weekly "Ready for review" digest email.'

    def handle(self, **options):
        send_weekly_ready_for_review_digest()
