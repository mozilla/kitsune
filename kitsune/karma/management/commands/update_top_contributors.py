from django.core.management.base import BaseCommand

from kitsune.karma.tasks import update_top_contributors


class Command(BaseCommand):
    help = "Update the top contributor lists and titles."

    def handle(self, **options):
        update_top_contributors()
