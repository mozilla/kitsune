from datetime import datetime
from datetime import timedelta

from django.core.management.base import BaseCommand

from kitsune.questions.models import Answer
from kitsune.search.tasks import index_task
from kitsune.search.utils import to_class_path
from kitsune.users.models import UserMappingType
from kitsune.wiki.models import Revision


class Command(BaseCommand):
    help = "Update the users (in ES) that contributed yesterday."

    def handle(self, **options):
        """
        The idea is to update the last_contribution_date field.
        """
        today = datetime.now()
        yesterday = today - timedelta(days=1)

        # Support Forum answers
        user_ids = list(Answer.objects.filter(
            created__gte=yesterday,
            created__lt=today).values_list('creator_id', flat=True))

        # KB Edits
        user_ids += list(Revision.objects.filter(
            created__gte=yesterday,
            created__lt=today).values_list('creator_id', flat=True))

        # KB Reviews
        user_ids += list(Revision.objects.filter(
            reviewed__gte=yesterday,
            reviewed__lt=today).values_list('reviewer_id', flat=True))

        # Note:
        # Army of Awesome replies are live indexed. No need to do anything here.

        index_task.delay(to_class_path(UserMappingType), list(set(user_ids)))
