import logging
import time
from datetime import datetime
from datetime import timedelta

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import connection
from django.db import transaction

from kitsune.questions.models import Question
from kitsune.questions.models import QuestionMappingType
from kitsune.search.es_utils import ES_EXCEPTIONS
from kitsune.search.es_utils import get_documents
from kitsune.search.tasks import index_task
from kitsune.search.utils import to_class_path

log = logging.getLogger('k.cron')


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
            .values_list('id', flat=True))

        if q_ids:
            log.info('Updating %d questions', len(q_ids))

            sql = """
                UPDATE questions_question
                SET is_archived = 1
                WHERE id IN (%s)
                """ % ','.join(map(str, q_ids))

            cursor = connection.cursor()
            cursor.execute(sql)
            if not transaction.get_connection().in_atomic_block:
                transaction.commit()

            if settings.ES_LIVE_INDEXING:
                try:
                    # So... the first time this runs, it'll handle 160K
                    # questions or so which stresses everything. Thus we
                    # do it in chunks because otherwise this won't work.
                    #
                    # After we've done this for the first time, we can nix
                    # the chunking code.

                    from kitsune.search.utils import chunked
                    for chunk in chunked(q_ids, 100):

                        # Fetch all the documents we need to update.
                        es_docs = get_documents(QuestionMappingType, chunk)

                        log.info('Updating %d index documents', len(es_docs))

                        documents = []

                        # For each document, update the data and stick it
                        # back in the index.
                        for doc in es_docs:
                            doc['question_is_archived'] = True
                            doc['indexed_on'] = int(time.time())
                            documents.append(doc)

                        QuestionMappingType.bulk_index(documents)

                except ES_EXCEPTIONS:
                    # Something happened with ES, so let's push index
                    # updating into an index_task which retries when it
                    # fails because of ES issues.
                    index_task.delay(to_class_path(QuestionMappingType), q_ids)
