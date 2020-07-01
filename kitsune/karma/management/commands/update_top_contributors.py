from django.core.management.base import BaseCommand

from kitsune.community.utils import top_contributors_questions
from kitsune.karma.models import Title


class Command(BaseCommand):
    help = "Update the top contributor lists and titles."

    def handle(self, **options):
        top25_ids = [x["user"]["id"] for x in top_contributors_questions(count=25)[0]]
        Title.objects.set_top10_contributors(top25_ids[:10])
        Title.objects.set_top25_contributors(top25_ids[10:25])
