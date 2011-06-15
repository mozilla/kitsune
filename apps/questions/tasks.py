import logging

from django.db import connection, transaction

from celery.decorators import task
from multidb.pinning import pin_this_thread, unpin_this_thread
from statsd import statsd

from activity.models import Action
from questions import ANSWERS_PER_PAGE


log = logging.getLogger('k.task')


@task(rate_limit='1/s')
def update_question_votes(q):
    log.debug('Got a new QuestionVote.')
    statsd.incr('questions.tasks.update')
    q.sync_num_votes_past_week()
    q.save(no_update=True, force_update=True)


@task(rate_limit='4/s')
def update_question_vote_chunk(data, **kwargs):
    """Update num_votes_past_week for a number of questions."""
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
    unpin_this_thread()
