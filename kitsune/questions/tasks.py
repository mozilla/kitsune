import logging
from datetime import date
from typing import Dict

# NOTE: This import is just so _fire_task gets registered with celery.
import tidings.events  # noqa
from celery import task
from django.conf import settings
from django.contrib.auth.models import User
from django.db import connection, transaction
from multidb.pinning import pin_this_thread, unpin_this_thread
from sentry_sdk import capture_exception

from kitsune.kbadge.utils import get_or_create_badge
from kitsune.questions.config import ANSWERS_PER_PAGE

log = logging.getLogger("k.task")


@task(rate_limit="1/s")
def update_question_votes(question_id):
    from kitsune.questions.models import Question

    log.debug("Got a new QuestionVote for question_id=%s." % question_id)

    # Pin to master db to avoid lag delay issues.
    pin_this_thread()

    try:
        q = Question.objects.get(id=question_id)
        q.sync_num_votes_past_week()
        q.save(force_update=True)
    except Question.DoesNotExist:
        log.info("Question id=%s deleted before task." % question_id)

    unpin_this_thread()


@task(rate_limit="4/s")
def update_question_vote_chunk(data):
    """Update num_votes_past_week for a number of questions."""

    # First we recalculate num_votes_past_week in the db.
    log.info("Calculating past week votes for %s questions." % len(data))

    ids = ",".join(map(str, data))
    sql = (
        """
        UPDATE questions_question q
        SET num_votes_past_week = (
            SELECT COUNT(created)
            FROM questions_questionvote qv
            WHERE qv.question_id = q.id
            AND qv.created >= DATE(SUBDATE(NOW(), 7))
        )
        WHERE q.id IN (%s);
        """
        % ids
    )
    cursor = connection.cursor()
    cursor.execute(sql)
    if not transaction.get_connection().in_atomic_block:
        transaction.commit()


@task(rate_limit="4/m")
def update_answer_pages(question_id: int):
    from kitsune.questions.models import Question

    try:
        question = Question.objects.get(id=question_id)
    except Question.DoesNotExist as err:
        capture_exception(err)
        return

    log.debug(
        "Recalculating answer page numbers for question %s: %s" % (question.pk, question.title)
    )

    i = 0
    answers = question.answers.using("default").order_by("created")
    for answer in answers.filter(is_spam=False):
        answer.page = i // ANSWERS_PER_PAGE + 1
        answer.save(no_notify=True)
        i += 1


@task()
def maybe_award_badge(badge_template: Dict, year: int, user_id: int):
    """Award the specific badge to the user if they've earned it."""
    badge = get_or_create_badge(badge_template, year)

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist as err:
        capture_exception(err)
        return

    # If the user already has the badge, there is nothing else to do.
    if badge.is_awarded_to(user):
        return

    # Count the number of replies tweeted in the current year.
    from kitsune.questions.models import Answer

    qs = Answer.objects.filter(
        creator=user, created__gte=date(year, 1, 1), created__lt=date(year + 1, 1, 1)
    )

    # If the count is at or above the limit, award the badge.
    if qs.count() >= settings.BADGE_LIMIT_SUPPORT_FORUM:
        badge.award_to(user)
        return True
