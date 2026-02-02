import logging
import textwrap
from datetime import date, datetime, timedelta

from celery import shared_task
from django.conf import settings
from django.contrib.auth.models import Group, User
from django.core.mail import send_mail
from django.db.models import Count, OuterRef, Subquery
from django.db.models.functions import Coalesce, Now
from django.utils import timezone
from sentry_sdk import capture_exception

from kitsune.community.utils import num_deleted_contributions
from kitsune.kbadge.utils import get_or_create_badge
from kitsune.questions.config import ANSWERS_PER_PAGE
from kitsune.questions.models import QuestionVisits
from kitsune.search.es_utils import index_objects_bulk
from kitsune.sumo.decorators import skip_if_read_only_mode
from kitsune.sumo.utils import chunked

log = logging.getLogger("k.task")


@shared_task(rate_limit="1/s")
@skip_if_read_only_mode
def update_question_votes(question_id):
    from kitsune.questions.models import Question

    log.debug("Got a new QuestionVote for question_id={}.".format(question_id))

    try:
        q = Question.objects.get(id=question_id)
        q.sync_num_votes_past_week()
        q.save(force_update=True)
    except Question.DoesNotExist:
        log.info("Question id={} deleted before task.".format(question_id))


@shared_task(rate_limit="4/s")
@skip_if_read_only_mode
def update_question_vote_chunk(question_ids: list[int]) -> None:
    """Given a list of questions, update the "num_votes_past_week" attribute of each one."""
    from kitsune.questions.models import Question, QuestionVote

    log.info("Calculating past week votes for {} questions.".format(len(question_ids)))

    past_week = (timezone.now() - timedelta(days=7)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )

    Question.objects.filter(id__in=question_ids).update(
        num_votes_past_week=Coalesce(
            Subquery(
                # Use "__range" to ensure the database index is used in Postgres.
                QuestionVote.objects.filter(
                    question_id=OuterRef("id"), created__range=(past_week, Now())
                )
                .order_by()
                .values("question_id")
                .annotate(count=Count("*"))
                .values("count")
            ),
            0,
        )
    )


@shared_task(rate_limit="4/m")
@skip_if_read_only_mode
def update_answer_pages(question_id: int):
    from kitsune.questions.models import Question

    try:
        question = Question.objects.get(id=question_id)
    except Question.DoesNotExist as err:
        capture_exception(err)
        return

    log.debug(f"Recalculating answer page numbers for question {question.pk}: {question.title}")

    i = 0
    answers = question.answers.using("default").order_by("created")
    for answer in answers.filter(is_spam=False):
        answer.page = i // ANSWERS_PER_PAGE + 1
        answer.save(no_notify=True)
        i += 1


@shared_task
@skip_if_read_only_mode
def maybe_award_badge(badge_template: dict, year: int, user_id: int) -> bool:
    """Award the specific badge to the user if they've earned it."""
    badge = get_or_create_badge(badge_template, year)

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist as err:
        capture_exception(err)
        return False

    # If the user already has the badge, there is nothing else to do.
    if badge.is_awarded_to(user):
        return False

    # Count the number of replies tweeted in the current year.
    from kitsune.questions.models import Answer

    num_contributions = Answer.objects.filter(
        creator=user, created__gte=date(year, 1, 1), created__lt=date(year + 1, 1, 1)
    ).count() + num_deleted_contributions(
        Answer,
        contributor=user,
        contribution_timestamp__gte=date(year, 1, 1),
        contribution_timestamp__lt=date(year + 1, 1, 1),
    )

    # If the count is at or above the limit, award the badge.
    if num_contributions >= settings.BADGE_LIMIT_SUPPORT_FORUM:
        badge.award_to(user)
        return True

    return False


@shared_task
@skip_if_read_only_mode
def cleanup_old_spam() -> None:
    """Clean up spam Questions and Answers older than the configured cutoff period."""
    from kitsune.questions.handlers import OldSpamCleanupHandler

    log.info("Starting cleanup of old spam content.")
    handler = OldSpamCleanupHandler()

    try:
        result = handler.cleanup_old_spam()
    except Exception as err:
        capture_exception(err)
        log.error(str(err))
    else:
        log.info(
            f"Spam cleanup completed: deleted {result['questions_deleted']} questions"
            f" and {result['answers_deleted']} answers marked as spam"
            f" before {result['cutoff_date']}"
        )


@shared_task
@skip_if_read_only_mode
def report_employee_answers() -> None:
    """
    We report on the users in the "Support Forum Tracked" group.
    We send the email to the users in the "Support Forum Metrics" group.
    """
    from kitsune.questions.models import Answer, Question

    tracked_group = Group.objects.get(name="Support Forum Tracked")
    report_group = Group.objects.get(name="Support Forum Metrics")

    tracked_users = tracked_group.user_set.all()
    report_recipients = report_group.user_set.all()

    if len(tracked_users) == 0 or len(report_recipients) == 0:
        return

    yesterday = date.today() - timedelta(days=1)
    day_before_yesterday = yesterday - timedelta(days=1)

    # Total number of questions asked the day before yesterday
    questions = Question.objects.filter(
        creator__is_active=True, created__gte=day_before_yesterday, created__lt=yesterday
    )
    num_questions = questions.count()

    # Total number of answered questions day before yesterday
    num_answered = questions.filter(num_answers__gt=0).count()

    # Total number of questions answered by user in tracked_group
    num_answered_by_tracked = {}
    for user in tracked_users:
        num_answered_by_tracked[user.username] = (
            Answer.objects.filter(question__in=questions, creator=user)
            .values_list("question_id")
            .distinct()
            .count()
        )

    email_subject = "Support Forum answered report for {date}".format(date=day_before_yesterday)

    email_body_tmpl = textwrap.dedent(
        """\
        Date: {date}
        Number of questions asked: {num_questions}
        Number of questions answered: {num_answered}
        """
    )
    email_body = email_body_tmpl.format(
        date=day_before_yesterday, num_questions=num_questions, num_answered=num_answered
    )

    for username, count in list(num_answered_by_tracked.items()):
        email_body += "Number of questions answered by {username}: {count}\n".format(
            username=username, count=count
        )

    email_addresses = [u.email for u in report_recipients]

    send_mail(
        email_subject,
        email_body,
        settings.TIDINGS_FROM_ADDRESS,
        email_addresses,
        fail_silently=False,
    )


@shared_task
@skip_if_read_only_mode
def update_weekly_votes() -> None:
    from kitsune.questions.models import Question, QuestionVote

    # Get all questions (id) with a vote in the last week.
    recent = timezone.now() - timedelta(days=7)
    q = QuestionVote.objects.filter(created__range=(recent, Now()))
    q = q.values_list("question_id", flat=True).order_by("question")
    q = q.distinct()
    q_with_recent_votes = list(q)

    # Get all questions with num_votes_past_week > 0
    q = Question.objects.filter(num_votes_past_week__gt=0)
    q = q.values_list("id", flat=True)
    q_with_nonzero_votes = list(q)

    # Union.
    qs_to_update = list(set(q_with_recent_votes + q_with_nonzero_votes))

    log.info(f"Started update of {len(qs_to_update)} questions.")

    # Chunk them for tasks.
    for chunk in chunked(qs_to_update, 50):
        update_question_vote_chunk.delay(chunk)


@shared_task
@skip_if_read_only_mode
def auto_archive_old_questions() -> None:
    from kitsune.questions.models import Answer, Question

    # Get a list of ids of questions we're going to go change. We need
    # a list of ids so that we can feed it to the update, but then
    # also know what we need to update in the index.
    days_180 = timezone.now() - timedelta(days=180)
    q_ids = list(
        Question.objects.filter(is_archived=False)
        # Use "__range" to ensure the database index is used in Postgres.
        .filter(created__range=(datetime.min, days_180))
        .values_list("id", flat=True)
    )

    if q_ids:
        log.info(f"Updating {len(q_ids)} questions")

        Question.objects.filter(id__in=q_ids).update(is_archived=True)

        if settings.ES_LIVE_INDEXING:
            answer_ids = list(
                Answer.objects.filter(question_id__in=q_ids).values_list("id", flat=True)
            )
            index_objects_bulk.delay("QuestionDocument", q_ids)
            index_objects_bulk.delay("AnswerDocument", answer_ids)


@shared_task
@skip_if_read_only_mode
def reload_question_traffic_stats(verbose: bool = True) -> None:
    QuestionVisits.reload_from_analytics(verbose=verbose)
