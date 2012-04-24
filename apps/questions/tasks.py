import logging

from django.conf import settings
from django.db import connection, transaction

from celery.decorators import task
from multidb.pinning import pin_this_thread, unpin_this_thread
from statsd import statsd

from activity.models import Action
from questions import ANSWERS_PER_PAGE
from questions.karma_actions import AnswerAction, FirstAnswerAction


log = logging.getLogger('k.task')


@task(rate_limit='1/s')
def update_question_votes(question_id):
    from questions.models import Question

    log.debug('Got a new QuestionVote for question_id=%s.' % question_id)
    statsd.incr('questions.tasks.update')

    # Pin to master db to avoid lag delay issues.
    pin_this_thread()

    try:
        q = Question.uncached.get(id=question_id)
        q.sync_num_votes_past_week()
        q.save(no_update=True, force_update=True)
    except Question.DoesNotExist:
        log.info('Question id=%s deleted before task.' % question_id)

    unpin_this_thread()


@task(rate_limit='4/s')
def update_question_vote_chunk(data, **kwargs):
    """Update num_votes_past_week for a number of questions."""

    # First we recalculate num_votes_past_week in the db.
    log.info('Calculating past week votes for %s questions.' % len(data))

    ids = ','.join(map(str, data))
    sql = """
        UPDATE questions_question q
        SET num_votes_past_week = (
            SELECT COUNT(created)
            FROM questions_questionvote qv
            WHERE qv.question_id = q.id
            AND qv.created >= DATE(SUBDATE(NOW(), 7))
        )
        WHERE q.id IN (%s);
        """ % ids
    cursor = connection.cursor()
    cursor.execute(sql)
    transaction.commit_unless_managed()

    # Next we update our index with the changes we made directly in
    # the db.
    if data and settings.ES_LIVE_INDEXING:
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

        # Fetch all the documents we need to update.
        from questions.models import Question
        from search import es_utils
        es_docs = es_utils.get_documents(Question, data)

        # For each document, update the data and stick it back in the
        # index.
        for doc in es_docs:
            # Note: Need to keep this in sync with
            # Question.extract_document.
            doc[u'num_votes_past_week'] = id_to_num[int(doc[u'id'])]

            Question.index(doc, refresh=True)


@task(rate_limit='4/m')
def update_answer_pages(question):
    log.debug('Recalculating answer page numbers for question %s: %s' %
              (question.pk, question.title))

    i = 0
    for answer in question.answers.using('default').order_by('created').all():
        answer.page = i / ANSWERS_PER_PAGE + 1
        answer.save(no_update=True, no_notify=True)
        i += 1


@task
def log_answer(answer):
    pin_this_thread()

    creator = answer.creator
    created = answer.created
    question = answer.question
    users = [a.creator for a in
             question.answers.select_related('creator').exclude(
                creator=creator)]
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
    if answer == answer.question.answers.order_by('created')[0]:
        FirstAnswerAction(answer.creator, answer.created.date()).save()

    unpin_this_thread()
