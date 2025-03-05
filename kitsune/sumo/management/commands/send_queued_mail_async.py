from django.core.management.base import BaseCommand
from post_office.tasks import queued_mail_handler


class Command(BaseCommand):

    def handle(self, *args, **options):
        """
        Queue the send_queued_mail() Celery task.
        """
        queued_mail_handler(None)
