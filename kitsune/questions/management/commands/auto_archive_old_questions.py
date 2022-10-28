import logging
from datetime import datetime, timedelta

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import connection, transaction

from kitsune.questions.models import Answer, Question
from kitsune.search.es_utils import index_objects_bulk

log = logging.getLogger("k.cron")


class Command(BaseCommand):
    help = "Archive all questions that were created over 180 days ago."

    def handle(self, **options):
        # Set up logging so it doesn't send Ricky email.
        logging.basicConfig(level=logging.ERROR)

        # Get a list of ids of questions we're going to go change. We need
        # a list of ids so that we can feed it to the update, but then
        # also know what we need to update in the index.
        days_180 = datetime.now() - timedelta(days=180)
        q_ids = list(
            Question.objects.filter(is_archived=False)
            .filter(created__lte=days_180)
            .values_list("id", flat=True)
        )

        if q_ids:
            log.info("Updating %d questions", len(q_ids))

            sql = """
                UPDATE questions_question
                SET is_archived = 1
                WHERE id IN (%s)
                """ % ",".join(
                map(str, q_ids)
            )

            with connection.cursor() as cursor:
                cursor.execute(sql)
            if not transaction.get_connection().in_atomic_block:
                transaction.commit()

            if settings.ES_LIVE_INDEXING:
                # elastic v7 code:
                answer_ids = list(
                    Answer.objects.filter(question_id__in=q_ids).values_list("id", flat=True)
                )
                index_objects_bulk.delay("QuestionDocument", q_ids)
                index_objects_bulk.delay("AnswerDocument", answer_ids)
