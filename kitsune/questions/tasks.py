import logging
from datetime import date

from django.conf import settings
from django.contrib.sites.models import Site
from django.db import connection, transaction

# NOTE: This import is just so _fire_task gets registered with celery.
import tidings.events
from celery.task import task
from multidb.pinning import pin_this_thread, unpin_this_thread
from statsd import statsd

from kitsune.kbadge.utils import get_or_create_badge
from kitsune.questions import ANSWERS_PER_PAGE
from kitsune.questions.karma_actions import AnswerAction, FirstAnswerAction
from kitsune.questions.marketplace import submit_ticket
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
def update_question_vote_chunk(data):
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

        try:
            # Fetch all the documents we need to update.
            from kitsune.questions.models import QuestionMappingType
            from kitsune.search import es_utils
            es_docs = es_utils.get_documents(QuestionMappingType, data)

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


@task
def maybe_award_badge(badge_template, year, user):
    """Award the specific badge to the user if they've earned it."""
    badge = get_or_create_badge(badge_template, year)

    # If the user already has the badge, there is nothing else to do.
    if badge.is_awarded_to(user):
        return

    # Count the number of replies tweeted in the current year.
    from kitsune.questions.models import Answer
    qs = Answer.objects.filter(
        creator=user,
        created__gte=date(year, 1, 1),
        created__lt=date(year + 1, 1, 1))

    # If the count is 30 or higher, award the badge.
    if qs.count() >= 30:
        badge.award_to(user)
        return True


@task
def escalate_question(question_id):
    """Escalate a question to zendesk by submitting a ticket."""
    from kitsune.questions.models import Question
    question = Question.objects.get(id=question_id)

    url = 'https://{domain}{url}'.format(
        domain=Site.objects.get_current().domain,
        url=question.get_absolute_url())

    submit_ticket(
        email='support@mozilla.com',
        category='Escalated',
        subject='[Escalated] {title}'.format(title=question.title),
        body='{url}\n\n{content}'.format(url=url, content=question.content))
