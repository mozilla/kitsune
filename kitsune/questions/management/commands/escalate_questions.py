from datetime import datetime, timedelta

from django.conf import settings
from django.core.management.base import BaseCommand

from kitsune.questions import config
from kitsune.questions.models import Question
from kitsune.questions.tasks import escalate_question


class Command(BaseCommand):
    help = "Escalate questions needing attention."

    def handle(self, **options):
        """
        Escalate questions where the status is "needs attention" and
        still have no replies after 24 hours, but not that are older
        than 25 hours (this runs every hour).
        """
        # Get all the questions that need attention and haven't been escalated.
        qs = Question.objects.needs_attention().exclude(
            tags__slug__in=[config.ESCALATE_TAG_NAME]
        )

        # Only include English.
        qs = qs.filter(locale=settings.WIKI_DEFAULT_LANGUAGE)

        # Exclude certain products.
        qs = qs.exclude(product__slug__in=config.ESCALATE_EXCLUDE_PRODUCTS)

        # Exclude those by inactive users.
        qs = qs.exclude(creator__is_active=False)

        # Filter them down to those that haven't been replied to and are over
        # 24 hours old but less than 25 hours old. We run this once an hour.
        start = datetime.now() - timedelta(hours=24)
        end = datetime.now() - timedelta(hours=25)
        qs_no_replies_yet = qs.filter(
            last_answer__isnull=True, created__lt=start, created__gt=end
        )

        for question in qs_no_replies_yet:
            escalate_question.delay(question.id)

        return str(len(qs_no_replies_yet))
