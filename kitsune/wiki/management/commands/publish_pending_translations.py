from django.core.management.base import BaseCommand

from kitsune.wiki.tasks import publish_pending_translations


class Command(BaseCommand):
    help = "Publish pending machine translations in hybrid-strategy locales."

    def handle(self, *args, **options):
        publish_pending_translations()
