from datetime import datetime, timedelta

from django.core import mail

import mock
from nose.tools import eq_

from kitsune.products.tests import product
import kitsune.questions.tasks
from kitsune.questions import config
from kitsune.questions.cron import escalate_questions, report_employee_answers
from kitsune.questions.tests import answer, question
from kitsune.sumo.tests import TestCase
from kitsune.users.models import Group
from kitsune.users.tests import user


class TestEscalateCron(TestCase):

    @mock.patch.object(kitsune.questions.tasks, 'submit_ticket')
    def test_escalate_questions_cron(self, submit_ticket):
        """Verify the escalate cronjob escalates the right questions."""

        questions_to_escalate = [
            # Questions over 24 hours old without an answer.
            question(
                created=datetime.now() - timedelta(hours=24, minutes=10),
                save=True),
            question(
                created=datetime.now() - timedelta(hours=24, minutes=50),
                save=True),
        ]

        # Question about Firefox OS
        fxos = product(slug='firefox-os', save=True)
        q = question(
            created=datetime.now() - timedelta(hours=24, minutes=10),
            product=fxos,
            save=True)
        questions_to_escalate.append(q)

        # Questions not to escalate

        # Questions newer than 24 hours without an answer.
        question(save=True)
        question(created=datetime.now() - timedelta(hours=11), save=True)
        question(created=datetime.now() - timedelta(hours=21), save=True)

        # Questions older than 25 hours (The cronjob runs once an hour)
        question(created=datetime.now() - timedelta(hours=26), save=True)

        # Question in the correct time range, but not in the default language.
        question(created=datetime.now() - timedelta(hours=24, minutes=10), locale='de', save=True)

        # Question older than 24 hours with a recent answer.
        q = question(
            created=datetime.now() - timedelta(hours=24, minutes=10),
            save=True)
        answer(created=datetime.now() - timedelta(hours=10), question=q,
               save=True)
        answer(created=datetime.now() - timedelta(hours=1), creator=q.creator,
               question=q, save=True)

        # Question older than 24 hours with a recent answer by the asker.
        q = question(
            created=datetime.now() - timedelta(hours=24, minutes=10),
            save=True)
        answer(
            created=datetime.now() - timedelta(hours=15), creator=q.creator,
            question=q, save=True)

        # Question older than 24 hours without an answer already escalated.
        q = question(
            created=datetime.now() - timedelta(hours=24, minutes=10),
            save=True)
        q.tags.add(config.ESCALATE_TAG_NAME)

        # Question with an inactive user.
        q = question(
            created=datetime.now() - timedelta(hours=24, minutes=10),
            save=True)
        q.creator.is_active = False
        q.creator.save()

        # Question about Thunderbird, which is one of the products we exclude.
        tb = product(slug='thunderbird', save=True)
        q = question(
            created=datetime.now() - timedelta(hours=24, minutes=10),
            product=tb,
            save=True)

        # Run the cron job and verify only 3 questions were escalated.
        eq_(len(questions_to_escalate), escalate_questions())


class TestEmployeeReportCron(TestCase):

    def test_report_employee_answers(self):
        # Note: This depends on two groups that are created in migrations.
        # If we fix the tests to not run migrations, we'll need to create the
        # two groups here: 'Support Forum Tracked', 'Support Forum Metrics'

        tracked_group = Group.objects.get(name='Support Forum Tracked')
        tracked_user = user(save=True)
        tracked_user.groups.add(tracked_group)

        report_group = Group.objects.get(name='Support Forum Metrics')
        report_user = user(save=True)
        report_user.groups.add(report_group)

        # An unanswered question that should get reported
        question(created=datetime.now() - timedelta(days=2), save=True)

        # An answered question that should get reported
        q = question(created=datetime.now() - timedelta(days=2), save=True)
        answer(question=q, save=True)

        # A question answered by a tracked user that should get reported
        q = question(created=datetime.now() - timedelta(days=2), save=True)
        answer(creator=tracked_user, question=q, save=True)

        # More questions that shouldn't get reported
        q = question(created=datetime.now() - timedelta(days=3), save=True)
        answer(creator=tracked_user, question=q, save=True)
        q = question(created=datetime.now() - timedelta(days=1), save=True)
        answer(question=q, save=True)
        question(save=True)

        report_employee_answers()

        # Get the last email and verify contents
        email = mail.outbox[len(mail.outbox) - 1]

        assert 'Number of questions asked: 3' in email.body
        assert 'Number of questions answered: 2' in email.body
        assert '{username}: 1'.format(username=tracked_user.username) in email.body

        eq_([report_user.email], email.to)
