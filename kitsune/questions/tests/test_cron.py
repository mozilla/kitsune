from datetime import datetime, timedelta

import mock
from nose.tools import eq_

from kitsune.products.tests import product
import kitsune.questions.tasks
from kitsune.questions import config
from kitsune.questions.cron import escalate_questions
from kitsune.questions.tests import answer, question
from kitsune.sumo.tests import TestCase


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
