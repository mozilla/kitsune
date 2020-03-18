from datetime import datetime, timedelta

import mock
from django.core import mail
from django.core.management import call_command
from nose.tools import eq_

import kitsune.questions.tasks
from kitsune.products.tests import ProductFactory
from kitsune.questions import config
from kitsune.questions.tests import AnswerFactory, QuestionFactory
from kitsune.sumo.tests import TestCase
from kitsune.users.models import Group
from kitsune.users.tests import UserFactory


class TestEscalateCron(TestCase):
    @mock.patch.object(kitsune.questions.tasks, "submit_ticket")
    def test_escalate_questions_cron(self, submit_ticket):
        """Verify the escalate cronjob escalates the right questions."""

        questions_to_escalate = [
            # Questions over 24 hours old without an answer.
            QuestionFactory(created=datetime.now() - timedelta(hours=24, minutes=10)),
            QuestionFactory(created=datetime.now() - timedelta(hours=24, minutes=50)),
        ]

        # Question about Firefox OS
        fxos = ProductFactory(slug="firefox-os")
        q = QuestionFactory(
            created=datetime.now() - timedelta(hours=24, minutes=10), product=fxos
        )
        questions_to_escalate.append(q)

        # Questions not to escalate

        # Questions newer than 24 hours without an answer.
        QuestionFactory()
        QuestionFactory(created=datetime.now() - timedelta(hours=11))
        QuestionFactory(created=datetime.now() - timedelta(hours=21))

        # Questions older than 25 hours (The cronjob runs once an hour)
        QuestionFactory(created=datetime.now() - timedelta(hours=26))

        # Question in the correct time range, but not in the default language.
        QuestionFactory(
            created=datetime.now() - timedelta(hours=24, minutes=10), locale="de"
        )

        # Question older than 24 hours with a recent answer.
        q = QuestionFactory(created=datetime.now() - timedelta(hours=24, minutes=10))
        AnswerFactory(created=datetime.now() - timedelta(hours=10), question=q)
        AnswerFactory(
            created=datetime.now() - timedelta(hours=1), creator=q.creator, question=q
        )

        # Question older than 24 hours with a recent answer by the asker.
        q = QuestionFactory(created=datetime.now() - timedelta(hours=24, minutes=10))
        AnswerFactory(
            created=datetime.now() - timedelta(hours=15), creator=q.creator, question=q
        )

        # Question older than 24 hours without an answer already escalated.
        q = QuestionFactory(created=datetime.now() - timedelta(hours=24, minutes=10))
        q.tags.add(config.ESCALATE_TAG_NAME)

        # Question with an inactive user.
        q = QuestionFactory(
            creator__is_active=False,
            created=datetime.now() - timedelta(hours=24, minutes=10),
        )

        # Question about Thunderbird, which is one of the products we exclude.
        tb = ProductFactory(slug="thunderbird")
        q = QuestionFactory(
            created=datetime.now() - timedelta(hours=24, minutes=10), product=tb
        )

        # Run the cron job and verify only 3 questions were escalated.
        eq_(str(len(questions_to_escalate)), call_command("escalate_questions"))


class TestEmployeeReportCron(TestCase):
    def test_report_employee_answers(self):
        # Note: This depends on two groups that are created in migrations.
        # If we fix the tests to not run migrations, we'll need to create the
        # two groups here: 'Support Forum Tracked', 'Support Forum Metrics'

        tracked_group = Group.objects.get(name="Support Forum Tracked")
        tracked_user = UserFactory()
        tracked_user.groups.add(tracked_group)

        report_group = Group.objects.get(name="Support Forum Metrics")
        report_user = UserFactory()
        report_user.groups.add(report_group)

        # An unanswered question that should get reported
        QuestionFactory(created=datetime.now() - timedelta(days=2))

        # An answered question that should get reported
        q = QuestionFactory(created=datetime.now() - timedelta(days=2))
        AnswerFactory(question=q)

        # A question answered by a tracked user that should get reported
        q = QuestionFactory(created=datetime.now() - timedelta(days=2))
        AnswerFactory(creator=tracked_user, question=q)

        # More questions that shouldn't get reported
        q = QuestionFactory(created=datetime.now() - timedelta(days=3))
        AnswerFactory(creator=tracked_user, question=q)
        q = QuestionFactory(created=datetime.now() - timedelta(days=1))
        AnswerFactory(question=q)
        QuestionFactory()

        call_command("report_employee_answers")

        # Get the last email and verify contents
        email = mail.outbox[len(mail.outbox) - 1]

        assert "Number of questions asked: 3" in email.body
        assert "Number of questions answered: 2" in email.body
        assert "{username}: 1".format(username=tracked_user.username) in email.body

        eq_([report_user.email], email.to)
