from datetime import datetime
from datetime import timedelta

from django.contrib.auth.models import Group
from django.core import mail
from django.core.management import call_command
from nose.tools import eq_

from kitsune.questions.tests import AnswerFactory
from kitsune.questions.tests import QuestionFactory
from kitsune.sumo.tests import TestCase
from kitsune.users.tests import UserFactory


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
