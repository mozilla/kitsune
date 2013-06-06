import logging
from datetime import datetime, timedelta

from django.conf import settings
from django.db import connection, transaction

from celery.task import task
from multidb.pinning import pin_this_thread, unpin_this_thread
from statsd import statsd

from kitsune.activity.models import Action
from kitsune.questions import ANSWERS_PER_PAGE
from kitsune.questions.karma_actions import AnswerAction, FirstAnswerAction
from kitsune.search.es_utils import ES_EXCEPTIONS
from kitsune.search.tasks import index_task


log = logging.getLogger('k.task')


@task(rate_limit='1/s')
def update_question_votes(question_id):
    from kitsune.questions.models import Question

    log.debug('Got a new QuestionVote for question_id=%s.' % question_id)
    statsd.incr('questions.tasks.update')

    # Pin to master db to avoid lag delay issues.
    pin_this_thread()

    try:
        q = Question.uncached.get(id=question_id)
        q.sync_num_votes_past_week()
        q.save(force_update=True)
    except Question.DoesNotExist:
        log.info('Question id=%s deleted before task.' % question_id)

    unpin_this_thread()


@task(rate_limit='4/s')
def update_all_question_votes():
    """Update num_votes_past_week."""

    # Query provided by :cyborgshadow. See
    # https://bugzilla.mozilla.org/show_bug.cgi?id=880344
    sql = """
        UPDATE questions_question q
            LEFT JOIN (
                SELECT q.id, COUNT(qv.created) votes
                FROM questions_question q
                INNER JOIN questions_questionvote qv
                ON q.id = qv.question_id
                AND qv.created >= CURDATE() - INTERVAL 7 day
                GROUP  BY q.id) qv
            ON q.id = qv.id
        SET q.num_votes_past_week = IF(qv.votes > 0, qv.votes, 0);
        """
    cursor = connection.cursor()
    cursor.execute(sql)
    transaction.commit_unless_managed()

    # Next we update our index with the changes we made directly in
    # the db.
    if settings.ES_LIVE_INDEXING:
        # Figure out the questions that need to be reindexed...
        from kitsune.questions.models import Question, QuestionVote

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

        # Union them!
        qs_to_update = list(set(q_with_recent_votes + q_with_nonzero_votes))
        ids = ','.join(map(str, qs_to_update))

        # First we recalculate num_votes_past_week in the db.
        log.info('Reindexing %s questions for vote counts.' %
                 len(qs_to_update))

        # Get the data we just updated from the database.
        sql = """
            SELECT id, num_votes_past_week
            FROM questions_question
            WHERE id in (%s);
            """ % ids
        cursor = connection.cursor()
        cursor.execute(sql)

        # Since this returns (id, num_votes_past_week) tuples, we can
        # convert that directly to a dict.
        id_to_num = dict(cursor.fetchall())

        try:
            # Fetch all the documents we need to update.
            from kitsune.questions.models import QuestionMappingType
            from kitsune.search import es_utils
            es_docs = es_utils.get_documents(QuestionMappingType, qs_to_update)

            # For each document, update the data and stick it back in the
            # index.
            for doc in es_docs:
                # Note: Need to keep this in sync with
                # Question.extract_document.
                num = id_to_num[int(doc[u'id'])]
                doc[u'question_num_votes_past_week'] = num

                QuestionMappingType.index(doc, id_=doc['id'])
        except ES_EXCEPTIONS:
            # Something happened with ES, so let's push index updating
            # into an index_task which retries when it fails because
            # of ES issues.
            index_task.delay(QuestionMappingType, id_to_num.keys())


@task(rate_limit='4/m')
def update_answer_pages(question):
    log.debug('Recalculating answer page numbers for question %s: %s' %
              (question.pk, question.title))

    i = 0
    for answer in question.answers.using('default').order_by('created').all():
        answer.page = i / ANSWERS_PER_PAGE + 1
        answer.save(no_notify=True)
        i += 1


@task
def log_answer(answer):
    pin_this_thread()

    creator = answer.creator
    created = answer.created
    question = answer.question
    users = [
        a.creator
        for a in question.answers.select_related('creator').exclude(
            creator=creator)
        ]
    if question.creator != creator:
        users += [question.creator]
    users = set(users)  # Remove duplicates.

    if users:
        action = Action.objects.create(
            creator=creator,
            created=created,
            url=answer.get_absolute_url(),
            content_object=answer,
            formatter_cls='questions.formatters.AnswerFormatter')
        action.users.add(*users)

    transaction.commit_unless_managed()

    # Record karma actions
    AnswerAction(answer.creator, answer.created.date()).save()
    try:
        from kitsune.questions.models import Answer
        answers = Answer.uncached.filter(question=answer.question_id)
        if answer == answers.order_by('created')[0]:
            FirstAnswerAction(answer.creator, answer.created.date()).save()
    except IndexError:
        # If we hit an IndexError, we assume this is the first answer.
        FirstAnswerAction(answer.creator, answer.created.date()).save()

    unpin_this_thread()
