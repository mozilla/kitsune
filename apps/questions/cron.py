import logging
from datetime import datetime, timedelta

from django.conf import settings
from django.contrib.auth.models import User
from django.core.cache import cache
from django.db import connection, transaction

import cronjobs

from questions.models import Question, QuestionVote, QuestionMappingType
from questions.tasks import update_question_vote_chunk
from search.es_utils import ES_EXCEPTIONS, get_documents
from search.tasks import index_task
from sumo.utils import chunked


log = logging.getLogger('k.cron')


@cronjobs.register
def update_weekly_votes():
    """Keep the num_votes_past_week value accurate."""

    # Get all questions (id) with a vote in the last week.
    recent = datetime.now() - timedelta(days=7)
    q = QuestionVote.objects.filter(created__gte=recent)
    q = q.values_list('question_id', flat=True).order_by('question')
    q = q.distinct()
    q_with_recent_votes = list(q)

    # Get all questions with num_votes_past_week > 0
    q = Question.objects.filter(num_votes_past_week__gt=0)
    q = q.values_list('id', flat=True)
    q_with_nonzero_votes = list(q)

    # Union.
    qs_to_update = list(set(q_with_recent_votes + q_with_nonzero_votes))

    # Chunk them for tasks.
    for chunk in chunked(qs_to_update, 50):
        update_question_vote_chunk.apply_async(args=[chunk])


# TODO: remove this and use the karma top list.
@cronjobs.register
def cache_top_contributors():
    """Compute the top contributors and store in cache."""
    sql = '''SELECT u.*, COUNT(*) AS num_solutions
             FROM auth_user AS u, questions_answer AS a,
                  questions_question AS q
             WHERE u.id = a.creator_id AND a.id = q.solution_id AND
                   a.created >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
             GROUP BY u.id
             ORDER BY num_solutions DESC
             LIMIT 10'''
    users = list(User.objects.raw(sql))
    cache.set(settings.TOP_CONTRIBUTORS_CACHE_KEY, users,
              settings.TOP_CONTRIBUTORS_CACHE_TIMEOUT)


@cronjobs.register
def auto_lock_old_questions():
    """Locks all questions that were created over 180 days ago"""
    # Set up logging so it doesn't send Ricky email.
    logging.basicConfig(level=logging.ERROR)

    # Get a list of ids of questions we're going to go change. We need
    # a list of ids so that we can feed it to the update, but then
    # also know what we need to update in the index.
    days_180 = datetime.now() - timedelta(days=180)
    q_ids = list(Question.objects.filter(is_locked=False)
                                 .filter(created__lte=days_180)
                                 .values_list('id', flat=True))

    if q_ids:
        log.info('Updating %d questions', len(q_ids))

        sql = """
            UPDATE questions_question
            SET is_locked = 1
            WHERE id IN (%s)
            """ % ','.join(map(str, q_ids))

        cursor = connection.cursor()
        cursor.execute(sql)
        transaction.commit_unless_managed()

        if settings.ES_LIVE_INDEXING:
            try:
                # So... the first time this runs, it'll handle 160K
                # questions or so which stresses everything. Thus we
                # do it in chunks because otherwise this won't work.
                #
                # After we've done this for the first time, we can nix
                # the chunking code.

                from search.utils import chunked
                for chunk in chunked(q_ids, 100):

                    # Fetch all the documents we need to update.
                    es_docs = get_documents(QuestionMappingType, chunk)

                    log.info('Updating %d index documents', len(es_docs))

                    documents = []

                    # For each document, update the data and stick it
                    # back in the index.
                    for doc in es_docs:
                        doc[u'question_is_locked'] = True
                        documents.append(doc)

                    QuestionMappingType.bulk_index(
                        documents, id_field='document_id')

            except ES_EXCEPTIONS:
                # Something happened with ES, so let's push index
                # updating into an index_task which retries when it
                # fails because of ES issues.
                index_task.delay(QuestionMappingType, q_ids)
