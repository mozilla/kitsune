from nose.tools import eq_

from groups.models import GroupProfile
from groups.tests import group_profile
from sumo.tests import TestCase
from sumo.urlresolvers import reverse
from users.tests import user, group, add_permission


class EditGroupProfileTests(TestCase):
    def setUp(self):
        super(EditGroupProfileTests, self).setUp()
        self.user = user(save=True)
        self.group_profile = group_profile(group=group(save=True), save=True)
        self.client.login(username=self.user.username, password='testpass')

    def _verify_get_and_post(self):
        slug = self.group_profile.slug
        # Verify GET
        r = self.client.get(reverse('groups.edit', args=[slug]), follow=True)
        eq_(r.status_code, 200)
        # Verify POST
        r = self.client.post(reverse('groups.edit', locale='en-US',
                                     args=[slug]),
                             {'information': '=new info='})
        eq_(r.status_code, 302)
        gp = GroupProfile.uncached.get(slug=slug)
        eq_(gp.information, '=new info=')

    def test_edit_with_perm(self):
        add_permission(self.user, GroupProfile, 'change_groupprofile')
        self._verify_get_and_post()

    def test_edit_as_leader(self):
        self.group_profile.leaders.add(self.user)
        self._verify_get_and_post()

    def test_edit_without_perm(self):
        slug = self.group_profile.slug
        # Try GET
        r = self.client.get(reverse('groups.edit', args=[slug]), follow=True)
        eq_(r.status_code, 403)
        # Try POST
        r = self.client.post(reverse('groups.edit', locale='en-US',
                                     args=[slug]),
                             {'information': '=new info='})
        eq_(r.status_code, 403)
