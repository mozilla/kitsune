import logging
import textwrap
import time
from datetime import date, datetime, timedelta

from django.conf import settings
from django.contrib.auth.models import Group
from django.core.mail import send_mail
from django.db import connection, transaction

import cronjobs

from kitsune.questions import config
from kitsune.questions.models import (
    Question, QuestionVote, QuestionMappingType, QuestionVisits, Answer)
from kitsune.questions.tasks import (
    escalate_question, update_question_vote_chunk)
from kitsune.search.es_utils import ES_EXCEPTIONS, get_documents
from kitsune.search.tasks import index_task
from kitsune.sumo.utils import chunked


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


@cronjobs.register
def auto_archive_old_questions():
    """Archive all questions that were created over 180 days ago"""
    # Set up logging so it doesn't send Ricky email.
    logging.basicConfig(level=logging.ERROR)

    # Get a list of ids of questions we're going to go change. We need
    # a list of ids so that we can feed it to the update, but then
    # also know what we need to update in the index.
    days_180 = datetime.now() - timedelta(days=180)
    q_ids = list(Question.objects.filter(is_archived=False)
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
                        doc[u'question_is_archived'] = True
                        doc[u'indexed_on'] = int(time.time())
                        documents.append(doc)

                    QuestionMappingType.bulk_index(documents)

            except ES_EXCEPTIONS:
                # Something happened with ES, so let's push index
                # updating into an index_task which retries when it
                # fails because of ES issues.
                index_task.delay(QuestionMappingType, q_ids)


@cronjobs.register
def reload_question_traffic_stats():
    """Reload question views from the analytics."""
    if settings.STAGE:
        return

    QuestionVisits.reload_from_analytics(verbose=settings.DEBUG)


@cronjobs.register
def escalate_questions():
    """Escalate questions needing attention.

    Escalate questions where the status is "needs attention" and
    still have no replies after 24 hours, but not that are older
    than 25 hours (this runs every hour).
    """
    if settings.STAGE:
        return
    # Get all the questions that need attention and haven't been escalated.
    qs = Question.objects.needs_attention().exclude(
        tags__slug__in=[config.ESCALATE_TAG_NAME])

    # Only include English.
    qs = qs.filter(locale=settings.WIKI_DEFAULT_LANGUAGE)

    # Exclude certain products.
    qs = qs.exclude(product__slug__in=config.ESCALATE_EXCLUDE_PRODUCTS)

    # Exclude those by inactive users.
    qs = qs.exclude(creator__is_active=False)

    # Filter them down to those that haven't been replied to and are over
    # 24 hours old but less than 25 hours old. We run this once an hour.
    start = datetime.now() - timedelta(hours=24)
    end = datetime.now() - timedelta(hours=25)
    qs_no_replies_yet = qs.filter(
        last_answer__isnull=True,
        created__lt=start,
        created__gt=end)

    for question in qs_no_replies_yet:
        escalate_question.delay(question.id)

    return len(qs_no_replies_yet)


@cronjobs.register
def report_employee_answers():
    """Send an email about employee answered questions.

    We report on the users in the "Support Forum Tracked" group.
    We send the email to the users in the "Support Forum Metrics" group.
    """
    tracked_group = Group.objects.get(name='Support Forum Tracked')
    report_group = Group.objects.get(name='Support Forum Metrics')

    tracked_users = tracked_group.user_set.all()
    report_recipients = report_group.user_set.all()

    if len(tracked_users) == 0 or len(report_recipients) == 0:
        return

    yesterday = date.today() - timedelta(days=1)
    day_before_yesterday = yesterday - timedelta(days=1)

    # Total number of questions asked the day before yesterday
    questions = Question.objects.filter(
        creator__is_active=True,
        created__gte=day_before_yesterday,
        created__lt=yesterday)
    num_questions = questions.count()

    # Total number of answered questions day before yesterday
    num_answered = questions.filter(num_answers__gt=0).count()

    # Total number of questions answered by user in tracked_group
    num_answered_by_tracked = {}
    for user in tracked_users:
        num_answered_by_tracked[user.username] = Answer.objects.filter(
            question__in=questions,
            creator=user).values_list('question_id').distinct().count()

    email_subject = 'Support Forum answered report for {date}'.format(date=day_before_yesterday)

    email_body_tmpl = textwrap.dedent("""\
        Date: {date}
        Number of questions asked: {num_questions}
        Number of questions answered: {num_answered}
        """)
    email_body = email_body_tmpl.format(
        date=day_before_yesterday,
        num_questions=num_questions,
        num_answered=num_answered)

    for username, count in num_answered_by_tracked.items():
        email_body += 'Number of questions answered by {username}: {count}\n'.format(
            username=username, count=count)

    email_addresses = [u.email for u in report_recipients]

    send_mail(email_subject, email_body, settings.TIDINGS_FROM_ADDRESS, email_addresses,
              fail_silently=False)
