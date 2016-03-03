import os

from django.core.files import File

from nose.tools import eq_

from kitsune.groups.models import GroupProfile
from kitsune.groups.tests import GroupProfileFactory
from kitsune.sumo.templatetags.jinja_helpers import urlparams
from kitsune.sumo.tests import TestCase
from kitsune.sumo.urlresolvers import reverse
from kitsune.users.tests import UserFactory, GroupFactory, add_permission


class EditGroupProfileTests(TestCase):
    def setUp(self):
        super(EditGroupProfileTests, self).setUp()
        self.user = UserFactory()
        self.group_profile = GroupProfileFactory()
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
        gp = GroupProfile.objects.get(slug=slug)
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


class EditAvatarTests(TestCase):
    def setUp(self):
        super(EditAvatarTests, self).setUp()
        self.user = UserFactory()
        add_permission(self.user, GroupProfile, 'change_groupprofile')
        self.group_profile = GroupProfileFactory()
        self.client.login(username=self.user.username, password='testpass')

    def tearDown(self):
        if self.group_profile.avatar:
            self.group_profile.avatar.delete()
        super(EditAvatarTests, self).tearDown()

    def test_upload_avatar(self):
        """Upload a group avatar."""
        with open('kitsune/upload/tests/media/test.jpg') as f:
            self.group_profile.avatar.save('test_old.jpg', File(f), save=True)
        assert self.group_profile.avatar.name.endswith('92b516.jpg')
        old_path = self.group_profile.avatar.path
        assert os.path.exists(old_path), 'Old avatar is not in place.'

        url = reverse('groups.edit_avatar', locale='en-US',
                      args=[self.group_profile.slug])
        with open('kitsune/upload/tests/media/test.jpg') as f:
            r = self.client.post(url, {'avatar': f})

        eq_(302, r.status_code)
        url = reverse('groups.profile', args=[self.group_profile.slug])
        eq_('http://testserver/en-US' + url, r['location'])
        assert not os.path.exists(old_path), 'Old avatar was not removed.'

    def test_delete_avatar(self):
        """Delete a group avatar."""
        self.test_upload_avatar()

        url = reverse('groups.delete_avatar', locale='en-US',
                      args=[self.group_profile.slug])
        r = self.client.get(url)
        eq_(200, r.status_code)
        r = self.client.post(url)
        eq_(302, r.status_code)
        url = reverse('groups.profile', args=[self.group_profile.slug])
        eq_('http://testserver/en-US' + url, r['location'])
        gp = GroupProfile.objects.get(slug=self.group_profile.slug)
        eq_('', gp.avatar.name)


class AddRemoveMemberTests(TestCase):
    def setUp(self):
        super(AddRemoveMemberTests, self).setUp()
        self.user = UserFactory()
        self.member = UserFactory()
        add_permission(self.user, GroupProfile, 'change_groupprofile')
        self.group_profile = GroupProfileFactory()
        self.client.login(username=self.user.username, password='testpass')

    def test_add_member(self):
        url = reverse('groups.add_member', locale='en-US',
                      args=[self.group_profile.slug])
        r = self.client.get(url)
        eq_(405, r.status_code)
        r = self.client.post(url, {'users': self.member.username})
        eq_(302, r.status_code)
        assert self.member in self.group_profile.group.user_set.all()

    def test_remove_member(self):
        self.member.groups.add(self.group_profile.group)
        url = reverse('groups.remove_member', locale='en-US',
                      args=[self.group_profile.slug, self.member.id])
        r = self.client.get(url)
        eq_(200, r.status_code)
        r = self.client.post(url)
        eq_(302, r.status_code)
        assert self.member not in self.group_profile.group.user_set.all()


class AddRemoveLeaderTests(TestCase):
    def setUp(self):
        super(AddRemoveLeaderTests, self).setUp()
        self.user = UserFactory()
        add_permission(self.user, GroupProfile, 'change_groupprofile')
        self.leader = UserFactory()
        self.group_profile = GroupProfileFactory()
        self.client.login(username=self.user.username, password='testpass')

    def test_add_leader(self):
        url = reverse('groups.add_leader', locale='en-US',
                      args=[self.group_profile.slug])
        r = self.client.get(url)
        eq_(405, r.status_code)
        r = self.client.post(url, {'users': self.leader.username})
        eq_(302, r.status_code)
        assert self.leader in self.group_profile.leaders.all()

    def test_remove_member(self):
        self.group_profile.leaders.add(self.leader)
        url = reverse('groups.remove_leader', locale='en-US',
                      args=[self.group_profile.slug, self.leader.id])
        r = self.client.get(url)
        eq_(200, r.status_code)
        r = self.client.post(url)
        eq_(302, r.status_code)
        assert self.leader not in self.group_profile.leaders.all()


class JoinContributorsTests(TestCase):
    def setUp(self):
        super(JoinContributorsTests, self).setUp()
        self.user = UserFactory()
        self.client.login(username=self.user.username, password='testpass')
        GroupFactory(name='Contributors')

    def test_join_contributors(self):
        next = reverse('groups.list')
        url = reverse('groups.join_contributors', locale='en-US')
        url = urlparams(url, next=next)
        r = self.client.get(url)
        eq_(405, r.status_code)
        r = self.client.post(url)
        eq_(302, r.status_code)
        eq_('http://testserver%s' % next, r['location'])
        assert self.user.groups.filter(name='Contributors').exists()
