from nose.tools import eq_

from kitsune.karma.helpers import karma_titles
from kitsune.karma.models import Title
from kitsune.users.tests import TestCase, user, group


class KarmaTitleHelperTests(TestCase):
    def setUp(self):
        super(KarmaTitleHelperTests, self).setUp()
        self.user = user(save=True)
        self.group = group(name='group', save=True)
        self.user.groups.add(self.group)

    def test_user_title(self):
        title = 'User Title'
        t = Title(name=title)
        t.save()
        t.users.add(self.user)
        titles = karma_titles(self.user)
        eq_(1, len(titles))
        eq_(title, titles[0].name)

    def test_group_title(self):
        title = 'Group Title'
        t = Title(name=title)
        t.save()
        t.groups.add(self.group)
        titles = karma_titles(self.user)
        eq_(1, len(titles))
        eq_(title, titles[0].name)

    def test_user_and_group_title(self):
        u_title = 'User Title'
        g_title = 'Group Title'
        t = Title(name=u_title)
        t.save()
        t.users.add(self.user)
        t = Title(name=g_title)
        t.save()
        t.groups.add(self.group)
        titles = [k.name for k in karma_titles(self.user)]
        eq_(2, len(titles))
        assert u_title in titles
        assert g_title in titles
