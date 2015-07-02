from datetime import date

from kitsune.kbadge.tests import badge
from kitsune.questions.models import Answer
from kitsune.questions.badges import QUESTIONS_BADGES
from kitsune.questions.tests import answer, question
from kitsune.sumo.tests import TestCase
from kitsune.users.tests import profile


class TestQuestionsBadges(TestCase):

    def test_answer_badge(self):
        """Verify the Support Forum Badge is awarded properly."""
        # Create the user and badge.
        year = date.today().year
        u = profile().user
        badge_template = QUESTIONS_BADGES['answer-badge']
        b = badge(
            slug=badge_template['slug'].format(year=year),
            title=badge_template['title'].format(year=year),
            description=badge_template['description'].format(year=year),
            save=True)

        # Create 29 answers.
        q = question(save=True)
        answers = []
        for i in range(28):
            answers.append(answer(question=q, creator=u))
        Answer.objects.bulk_create(answers)

        # Create the 29th answer separately so the signals are triggered.
        answer(creator=u, save=True)

        # User should NOT have the badge yet.
        assert not b.is_awarded_to(u)

        # Create 1 more answer.
        answer(creator=u, save=True)

        # User should have the badge now.
        assert b.is_awarded_to(u)
