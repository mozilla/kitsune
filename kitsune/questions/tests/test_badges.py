from datetime import date

from django.conf import settings

from kitsune.kbadge.tests import BadgeFactory
from kitsune.questions.badges import QUESTIONS_BADGES
from kitsune.questions.tests import AnswerFactory
from kitsune.sumo.tests import TestCase
from kitsune.users.tests import UserFactory


class TestQuestionsBadges(TestCase):
    def test_answer_badge(self):
        """Verify the Support Forum Badge is awarded properly."""
        # Create the user and badge.
        year = date.today().year
        u = UserFactory()
        badge_template = QUESTIONS_BADGES["answer-badge"]
        b = BadgeFactory(
            slug=badge_template["slug"].format(year=year),
            title=badge_template["title"].format(year=year),
            description=badge_template["description"].format(year=year),
        )

        # Create one less answer than reqiured to earn badge
        AnswerFactory.create_batch(settings.BADGE_LIMIT_SUPPORT_FORUM - 1, creator=u)

        # User should NOT have the badge yet.
        assert not b.is_awarded_to(u)

        # Create 1 more answer.
        AnswerFactory(creator=u)

        # User should have the badge now.
        assert b.is_awarded_to(u)
