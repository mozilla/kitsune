from nose.tools import eq_

from kitsune.karma.models import Title
from kitsune.users.tests import TestCase, user


class KarmaTitleTests(TestCase):
    def test_top_contributors_title(self):
        # Set top 10 title to 3 users and verify
        title = 'Top 10 Contributor'
        u1 = user(save=True)
        u2 = user(save=True)
        u3 = user(save=True)
        Title.objects.set_top10_contributors([u1, u2, u3])
        top10_title = Title.objects.get(name=title)
        assert top10_title.is_auto
        eq_(3, len(top10_title.users.all()))

        # Update title to different list of users
        u4 = user(save=True)
        Title.objects.set_top10_contributors([u1, u3, u4])
        top10_title = Title.uncached.get(name=title)
        assert top10_title.is_auto
        eq_(3, len(top10_title.users.all()))
        assert u4 in top10_title.users.all()
        assert u2 not in top10_title.users.all()
