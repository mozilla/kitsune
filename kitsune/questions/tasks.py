import logging
from datetime import date
from typing import Dict

import tidings.events  # noqa
from celery import task
from django.conf import settings
from django.contrib.auth.models import User
from django.db import connection
from django.db import transaction
from multidb.pinning import pin_this_thread
from multidb.pinning import unpin_this_thread
from sentry_sdk import capture_exception

from kitsune.kbadge.utils import get_or_create_badge
from kitsune.questions.config import ANSWERS_PER_PAGE
from kitsune.search.es_utils import ES_EXCEPTIONS
from kitsune.search.tasks import index_task
from kitsune.search.utils import to_class_path
# NOTE: This import is just so _fire_task gets registered with celery.

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

    # Next we update our index with the changes we made directly in
    # the db.
    if data and settings.ES_LIVE_INDEXING:
        # Get the data we just updated from the database.
        sql = (
            """
            SELECT id, num_votes_past_week
            FROM questions_question
            WHERE id in (%s);
            """
            % ids
        )
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
                num = id_to_num[int(doc["id"])]
                doc["question_num_votes_past_week"] = num

                QuestionMappingType.index(doc, id_=doc["id"])
        except ES_EXCEPTIONS:
            # Something happened with ES, so let's push index updating
            # into an index_task which retries when it fails because
            # of ES issues.
            index_task.delay(to_class_path(QuestionMappingType), list(id_to_num.keys()))


@task(rate_limit="4/m")
def update_answer_pages(question_id: int):
    from kitsune.questions.models import Question
    try:
        question = Question.objects.get(id=question_id)
    except Question.DoesNotExist as err:
        capture_exception(err)
        return

    log.debug(
        "Recalculating answer page numbers for question %s: %s"
        % (question.pk, question.title)
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
