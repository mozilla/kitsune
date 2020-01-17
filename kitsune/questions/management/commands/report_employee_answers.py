import textwrap
from datetime import date, timedelta

from django.conf import settings
from django.contrib.auth.models import Group
from django.core.mail import send_mail
from django.core.management.base import BaseCommand

from kitsune.questions.models import (Answer, Question)


class Command(BaseCommand):
    help = "Send an email about employee answered questions."

    def handle(self, **options):
        """
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

        email_subject = 'Support Forum answered report for {date}'.format(
            date=day_before_yesterday)

        email_body_tmpl = textwrap.dedent("""\
            Date: {date}
            Number of questions asked: {num_questions}
            Number of questions answered: {num_answered}
            """)
        email_body = email_body_tmpl.format(
            date=day_before_yesterday,
            num_questions=num_questions,
            num_answered=num_answered)

        for username, count in list(num_answered_by_tracked.items()):
            email_body += 'Number of questions answered by {username}: {count}\n'.format(
                username=username, count=count)

        email_addresses = [u.email for u in report_recipients]

        send_mail(
            email_subject, email_body, settings.TIDINGS_FROM_ADDRESS, email_addresses,
            fail_silently=False)
