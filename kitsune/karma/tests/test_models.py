from kitsune.karma.models import Title
from kitsune.sumo.tests import TestCase
from kitsune.users.tests import UserFactory


class KarmaTitleTests(TestCase):
    def test_top_contributors_title(self):
        # Set top 10 title to 3 users and verify
        title = "Top 10 Contributor"
        u1 = UserFactory()
        u2 = UserFactory()
        u3 = UserFactory()
        Title.objects.set_top10_contributors([u1.id, u2.id, u3.id])
        top10_title = Title.objects.get(name=title)
        assert top10_title.is_auto
        self.assertEqual(3, len(top10_title.users.all()))

        # Update title to different list of users
        u4 = UserFactory()
        Title.objects.set_top10_contributors([u1.id, u3.id, u4.id])
        top10_title = Title.objects.get(name=title)
        assert top10_title.is_auto
        self.assertEqual(3, len(top10_title.users.all()))
        assert u4 in top10_title.users.all()
        assert u2 not in top10_title.users.all()
