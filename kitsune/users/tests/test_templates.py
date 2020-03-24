import os
from copy import copy

from django.conf import settings
from django.core.files import File
from django.test import override_settings
from nose.tools import eq_
from pyquery import PyQuery as pq
from tidings.models import Watch

from kitsune.flagit.models import FlaggedObject
from kitsune.kbadge.tests import AwardFactory, BadgeFactory
from kitsune.questions.events import QuestionReplyEvent
from kitsune.questions.tests import QuestionFactory
from kitsune.sumo.tests import get
from kitsune.sumo.urlresolvers import reverse
from kitsune.users.models import Profile
from kitsune.users.tests import TestCaseBase, UserFactory, add_permission
from kitsune.wiki.tests import RevisionFactory


class EditProfileTests(TestCaseBase):

    def test_edit_my_ProfileFactory(self):
        u = UserFactory()
        url = reverse('users.edit_my_profile')
        self.client.login(username=u.username, password='testpass')
        data = {'name': 'John Doe',
                'public_email': True,
                'bio': 'my bio',
                'website': 'http://google.com/',
                'twitter': '',
                'facebook': '',
                'mozillians': '',
                'irc_handle': 'johndoe',
                'timezone': 'America/New_York',
                'country': 'US',
                'city': 'Disney World',
                'locale': 'en-US'}
        r = self.client.post(url, data)
        eq_(302, r.status_code)
        profile = Profile.objects.get(user=u)
        for key in data:
            if key != 'timezone':
                assert data[key] == getattr(profile, key), (
                    "%r != %r (for key '%s')" % (data[key], getattr(profile, key), key))

        eq_(data['timezone'], profile.timezone.zone)

    def test_user_cant_edit_others_profile_without_permission(self):
        u1 = UserFactory()
        url = reverse('users.edit_profile', args=[u1.username])

        u2 = UserFactory()
        self.client.login(username=u2.username, password='testpass')

        # Try GET
        r = self.client.get(url)
        eq_(403, r.status_code)

        # Try POST
        r = self.client.post(url, {})
        eq_(403, r.status_code)

    def test_user_can_edit_others_profile_with_permission(self):
        u1 = UserFactory()
        url = reverse('users.edit_profile', args=[u1.username])

        u2 = UserFactory()
        add_permission(u2, Profile, 'change_profile')
        self.client.login(username=u2.username, password='testpass')

        # Try GET
        r = self.client.get(url)
        eq_(200, r.status_code)

        # Try POST
        data = {'name': 'John Doe',
                'public_email': True,
                'bio': 'my bio',
                'website': 'http://google.com/',
                'twitter': '',
                'facebook': '',
                'mozillians': '',
                'irc_handle': 'johndoe',
                'timezone': 'America/New_York',
                'country': 'US',
                'city': 'Disney World',
                'locale': 'en-US'}
        r = self.client.post(url, data)
        eq_(302, r.status_code)
        profile = Profile.objects.get(user=u1)
        for key in data:
            if key != 'timezone':
                assert data[key] == getattr(profile, key), (
                    "%r != %r (for key '%s')" % (data[key], getattr(profile, key), key))

        eq_(data['timezone'], profile.timezone.zone)


class EditAvatarTests(TestCaseBase):

    def setUp(self):
        super(EditAvatarTests, self).setUp()
        self.old_settings = copy(settings._wrapped.__dict__)
        self.u = UserFactory()

    def tearDown(self):
        settings._wrapped.__dict__ = self.old_settings
        user_profile = Profile.objects.get(user__username=self.u.username)
        if user_profile.avatar:
            user_profile.avatar.delete()
        super(EditAvatarTests, self).tearDown()

    @override_settings(MAX_AVATAR_FILE_SIZE=1024)
    def test_large_avatar(self):
        url = reverse('users.edit_avatar')
        self.client.login(username=self.u.username, password='testpass')
        with open('kitsune/upload/tests/media/test.jpg') as f:
            r = self.client.post(url, {'avatar': f})
        eq_(200, r.status_code)
        doc = pq(r.content)
        eq_('"test.jpg" is too large (12KB), the limit is 1KB',
            doc('.errorlist').text())

    def test_avatar_extensions(self):
        url = reverse('users.edit_avatar')
        self.client.login(username=self.u.username, password='testpass')
        with open('kitsune/upload/tests/media/test_invalid.ext') as f:
            r = self.client.post(url, {'avatar': f})
        eq_(200, r.status_code)
        doc = pq(r.content)
        assert doc('.errorlist').text().startswith(
            "File extension 'ext' is not allowed. Allowed extensions are:")

    def test_upload_avatar(self):
        """Upload a valid avatar."""
        user_profile = Profile.objects.get(user__username=self.u.username)
        with open('kitsune/upload/tests/media/test.jpg') as f:
            user_profile.avatar.save('test_old.jpg', File(f), save=True)
        assert user_profile.avatar.name.endswith('92b516.jpg')
        old_path = user_profile.avatar.path
        assert os.path.exists(old_path), 'Old avatar is not in place.'

        url = reverse('users.edit_avatar')
        self.client.login(username=self.u.username, password='testpass')
        with open('kitsune/upload/tests/media/test.jpg') as f:
            r = self.client.post(url, {'avatar': f})

        eq_(302, r.status_code)
        eq_('/en-US' + reverse('users.edit_my_profile'), r['location'])
        assert not os.path.exists(old_path), 'Old avatar was not removed.'

    def test_delete_avatar(self):
        """Delete an avatar."""
        self.test_upload_avatar()

        url = reverse('users.delete_avatar')
        self.client.login(username=self.u.username, password='testpass')
        r = self.client.post(url)

        user_profile = Profile.objects.get(user__username=self.u.username)
        eq_(302, r.status_code)
        eq_('/en-US' + reverse('users.edit_my_profile'), r['location'])
        eq_('', user_profile.avatar.name)


class ViewProfileTests(TestCaseBase):

    def setUp(self):
        self.u = UserFactory(profile__name='', profile__website='')
        self.profile = self.u.profile

    def test_view_ProfileFactory(self):
        r = self.client.get(reverse('users.profile', args=[self.u.username]))
        eq_(200, r.status_code)
        doc = pq(r.content)
        eq_(0, doc('#edit-profile-link').length)
        eq_(self.u.username, doc('h1.user').text())
        # No name set => no optional fields.
        eq_(0, doc('.contact').length)
        # Check canonical url
        eq_('%s/en-US/user/%s' % (settings.CANONICAL_URL, self.u.username),
            doc('link[rel="canonical"]')[0].attrib['href'])

    def test_view_profile_mine(self):
        """Logged in, on my profile, I see an edit link."""
        self.client.login(username=self.u.username, password='testpass')
        r = self.client.get(reverse('users.profile', args=[self.u.username]))
        eq_(200, r.status_code)
        doc = pq(r.content)
        eq_('Manage watch list', doc('#user-nav li:last').text())
        self.client.logout()

    def test_bio_links_nofollow(self):
        self.profile.bio = 'http://getseo.com, [http://getseo.com]'
        self.profile.save()
        r = self.client.get(reverse('users.profile', args=[self.u.username]))
        eq_(200, r.status_code)
        doc = pq(r.content)
        eq_(2, len(doc('.bio a[rel="nofollow"]')))

    def test_bio_links_no_img(self):
        # bug 1427813
        self.profile.bio = '<p>my dude image <img src="https://www.example.com/the-dude.jpg"></p>'
        self.profile.save()
        r = self.client.get(reverse('users.profile', args=[self.u.username]))
        eq_(200, r.status_code)
        assert '<p>my dude image </p>' in r.content

    def test_num_documents(self):
        """Verify the number of documents contributed by user."""
        u = UserFactory()
        RevisionFactory(creator=u)
        RevisionFactory(creator=u)

        r = self.client.get(reverse('users.profile', args=[u.username]))
        eq_(200, r.status_code)
        assert '2 documents' in r.content

    def test_deactivate_button(self):
        """Check that the deactivate button is shown appropriately"""
        u = UserFactory()
        r = self.client.get(reverse('users.profile', args=[u.username]))
        assert 'Deactivate this user' not in r.content

        add_permission(self.u, Profile, 'deactivate_users')
        self.client.login(username=self.u.username, password='testpass')
        r = self.client.get(reverse('users.profile', args=[u.username]))
        assert 'Deactivate this user' in r.content

        u.is_active = False
        u.save()
        r = self.client.get(reverse('users.profile', args=[u.username]))
        assert 'This user has been deactivated.' in r.content

        r = self.client.get(reverse('users.profile', args=[self.u.username]))
        assert 'Deactivate this user' not in r.content

    def test_badges_listed(self):
        """Verify that awarded badges appear on the profile page."""
        badge_title = 'awesomesauce badge'
        b = BadgeFactory(title=badge_title)
        u = UserFactory()
        AwardFactory(user=u, badge=b)
        r = self.client.get(reverse('users.profile', args=[u.username]))
        assert badge_title in r.content


class FlagProfileTests(TestCaseBase):

    def test_flagged_and_deleted_ProfileFactory(self):
        u = UserFactory()
        p = u.profile
        flag_user = UserFactory()
        # Flag a profile and delete it
        f = FlaggedObject(content_object=p,
                          reason='spam', creator_id=flag_user.id)
        f.save()
        p.delete()

        # Verify flagit queue
        u = UserFactory()
        add_permission(u, FlaggedObject, 'can_moderate')
        self.client.login(username=u.username, password='testpass')
        response = get(self.client, 'flagit.queue')
        eq_(200, response.status_code)
        doc = pq(response.content)
        eq_(1, len(doc('#flagged-queue form.update')))


class EditWatchListTests(TestCaseBase):
    """Test manage watch list"""

    def setUp(self):
        self.user = UserFactory()
        self.client.login(username=self.user.username, password='testpass')

        self.question = QuestionFactory(creator=self.user)
        QuestionReplyEvent.notify(self.user, self.question)

    def test_GET(self):
        r = self.client.get(reverse('users.edit_watch_list'))
        eq_(200, r.status_code)
        assert u'question: ' + self.question.title in r.content.decode('utf8')

    def test_POST(self):
        w = Watch.objects.get(object_id=self.question.id, user=self.user)
        eq_(w.is_active, True)

        self.client.post(reverse('users.edit_watch_list'))
        w = Watch.objects.get(object_id=self.question.id, user=self.user)
        eq_(w.is_active, False)

        self.client.post(reverse('users.edit_watch_list'), {
            'watch_%s' % w.id: '1'})
        w = Watch.objects.get(object_id=self.question.id, user=self.user)
        eq_(w.is_active, True)
