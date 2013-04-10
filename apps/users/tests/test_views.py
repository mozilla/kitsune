import os

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.core import mail
from django.test.utils import override_settings

import mock
from nose.tools import eq_
from pyquery import PyQuery as pq
from tidings.tests import watch

from questions.models import Question
from sumo.tests import TestCase, LocalizingClient, send_mail_raise_smtp
from sumo.urlresolvers import reverse
from users import ERROR_SEND_EMAIL
from users.models import (Profile, RegistrationProfile, EmailChange, Setting,
                          email_utils)
from users.tests import profile, user, group, add_permission


class RegisterTests(TestCase):
    def setUp(self):
        self.client.logout()
        super(RegisterTests, self).setUp()

    @override_settings(DEBUG=True)
    @mock.patch.object(Site.objects, 'get_current')
    def test_new_user(self, get_current):
        get_current.return_value.domain = 'su.mo.com'
        response = self.client.post(reverse('users.register', locale='en-US'),
                                    {'username': 'newbie',
                                     'email': 'newbie@example.com',
                                     'password': 'foobar22',
                                     'password2': 'foobar22'}, follow=True)
        eq_(200, response.status_code)
        u = User.objects.get(username='newbie')
        assert u.password.startswith('sha256')
        assert not u.is_active
        eq_(1, len(mail.outbox))
        assert mail.outbox[0].subject.find('Please confirm your') == 0
        key = RegistrationProfile.objects.all()[0].activation_key
        assert mail.outbox[0].body.find('activate/%s/%s' % (u.id, key)) > 0

        # By default, users aren't added to any groups
        eq_(0, len(u.groups.all()))

        # Now try to log in
        u.is_active = True
        u.save()
        response = self.client.post(reverse('users.login', locale='en-US'),
                                    {'username': 'newbie',
                                     'password': 'foobar22'}, follow=True)
        eq_(200, response.status_code)
        eq_('http://testserver/en-US/home?fpa=1',
            response.redirect_chain[0][0])

    @override_settings(DEBUG=True)
    @mock.patch.object(email_utils, 'send_messages')
    @mock.patch.object(Site.objects, 'get_current')
    def test_new_user_smtp_error(self, get_current, send_messages):
        get_current.return_value.domain = 'su.mo.com'

        send_messages.side_effect = send_mail_raise_smtp
        response = self.client.post(reverse('users.register', locale='en-US'),
                                    {'username': 'newbie',
                                     'email': 'newbie@example.com',
                                     'password': 'foobar22',
                                     'password2': 'foobar22'}, follow=True)
        self.assertContains(response, unicode(ERROR_SEND_EMAIL))
        assert not User.objects.filter(username='newbie').exists()

    @override_settings(DEBUG=True)
    @mock.patch.object(Site.objects, 'get_current')
    def test_unicode_password(self, get_current):
        u_str = u'a1\xe5\xe5\xee\xe9\xf8\xe7\u6709\u52b9'
        get_current.return_value.domain = 'su.mo.com'
        response = self.client.post(reverse('users.register', locale='ja'),
                                    {'username': 'cjkuser',
                                     'email': 'cjkuser@example.com',
                                     'password': u_str,
                                     'password2': u_str}, follow=True)
        eq_(200, response.status_code)
        u = User.objects.get(username='cjkuser')
        u.is_active = True
        u.save()
        assert u.password.startswith('sha256')

        # make sure you can login now
        response = self.client.post(reverse('users.login', locale='ja'),
                                    {'username': 'cjkuser',
                                     'password': u_str}, follow=True)
        eq_(200, response.status_code)
        eq_('http://testserver/ja/home?fpa=1', response.redirect_chain[0][0])

    @mock.patch.object(Site.objects, 'get_current')
    def test_new_user_activation(self, get_current):
        get_current.return_value.domain = 'su.mo.com'
        user_ = RegistrationProfile.objects.create_inactive_user(
            'sumouser1234', 'testpass', 'sumouser@test.com')
        assert not user_.is_active
        key = RegistrationProfile.objects.all()[0].activation_key
        url = reverse('users.activate', args=[user_.id, key])
        response = self.client.get(url, follow=True)
        eq_(200, response.status_code)
        user_ = User.objects.get(pk=user_.pk)
        assert user_.is_active

    @mock.patch.object(Site.objects, 'get_current')
    def test_new_user_claim_watches(self, get_current):
        """Claim user watches upon activation."""
        watch(email='sumouser@test.com', save=True)

        get_current.return_value.domain = 'su.mo.com'
        user_ = RegistrationProfile.objects.create_inactive_user(
            'sumouser1234', 'testpass', 'sumouser@test.com')
        key = RegistrationProfile.objects.all()[0].activation_key
        self.client.get(reverse('users.activate', args=[user_.id, key]),
                        follow=True)

        # Watches are claimed.
        assert user_.watch_set.exists()

    @mock.patch.object(Site.objects, 'get_current')
    def test_new_user_with_questions(self, get_current):
        """The user's questions are mentioned on the confirmation page."""
        get_current.return_value.domain = 'su.mo.com'
        # TODO: remove this test once we drop unconfirmed questions.
        user_ = RegistrationProfile.objects.create_inactive_user(
            'sumouser1234', 'testpass', 'sumouser@test.com')

        # Before we activate, let's create a question.
        q = Question.objects.create(title='test_question', creator=user_,
                                    content='test')

        # Activate account.
        key = RegistrationProfile.objects.all()[0].activation_key
        url = reverse('users.activate', args=[user_.id, key])
        response = self.client.get(url, follow=True)
        eq_(200, response.status_code)

        q = Question.objects.get(creator=user_)
        # Question is listed on the confirmation page.
        assert 'test_question' in response.content
        assert q.get_absolute_url() in response.content

    @override_settings(DEBUG=True)
    def test_duplicate_username(self):
        u = user(save=True)
        response = self.client.post(reverse('users.register', locale='en-US'),
                                    {'username': u.username,
                                     'email': 'newbie@example.com',
                                     'password': 'foo',
                                     'password2': 'foo'}, follow=True)
        self.assertContains(response, 'already exists')

    @override_settings(DEBUG=True)
    def test_duplicate_email(self):
        u = user(email='noob@example.com', save=True)
        User.objects.create(username='noob', email='noob@example.com').save()
        response = self.client.post(reverse('users.register', locale='en-US'),
                                    {'username': 'newbie',
                                     'email': u.email,
                                     'password': 'foo',
                                     'password2': 'foo'}, follow=True)
        self.assertContains(response, 'already exists')

    @override_settings(DEBUG=True)
    def test_no_match_passwords(self):
        u = user(save=True)
        response = self.client.post(reverse('users.register', locale='en-US'),
                                    {'username': u.username,
                                     'email': u.email,
                                     'password': 'testpass',
                                     'password2': 'testbus'}, follow=True)
        self.assertContains(response, 'must match')

    @mock.patch.object(Site.objects, 'get_current')
    def test_active_user_activation(self, get_current):
        """If an already active user tries to activate with a valid key,
        we take them to login page and show message."""
        get_current.return_value.domain = 'su.mo.com'
        user = RegistrationProfile.objects.create_inactive_user(
            'sumouser1234', 'testpass', 'sumouser@test.com')
        user.is_active = True
        user.save()
        key = RegistrationProfile.objects.all()[0].activation_key
        url = reverse('users.activate', args=[user.id, key])
        response = self.client.get(url, follow=True)
        eq_(200, response.status_code)
        doc = pq(response.content)
        eq_('Your account is already activated, log in below.',
            doc('ul.user-messages').text())

    @mock.patch.object(Site.objects, 'get_current')
    def test_old_activation_url(self, get_current):
        get_current.return_value.domain = 'su.mo.com'
        user = RegistrationProfile.objects.create_inactive_user(
            'sumouser1234', 'testpass', 'sumouser@test.com')
        assert not user.is_active
        key = RegistrationProfile.objects.all()[0].activation_key
        url = reverse('users.old_activate', args=[key])
        response = self.client.get(url, follow=True)
        eq_(200, response.status_code)
        user = User.objects.get(pk=user.pk)
        assert user.is_active

    @override_settings(DEBUG=True)
    @mock.patch.object(Site.objects, 'get_current')
    def test_new_contributor(self, get_current):
        """Verify that interested contributors are added to group."""
        get_current.return_value.domain = 'su.mo.com'
        group_name = 'Registered as contributor'
        group(name=group_name, save=True)
        data = {
            'username': 'newbie',
            'email': 'newbie@example.com',
            'password': 'foobar22',
            'password2': 'foobar22',
            'interested': 'yes'}
        response = self.client.post(reverse('users.register', locale='en-US'),
                                    data, follow=True)
        eq_(200, response.status_code)
        u = User.objects.get(username='newbie')
        eq_(group_name, u.groups.all()[0].name)

        # Activate user and verify email is sent.
        key = RegistrationProfile.objects.all()[0].activation_key
        url = reverse('users.activate', args=[u.id, key])
        response = self.client.get(url, follow=True)
        eq_(200, response.status_code)
        eq_(2, len(mail.outbox))
        assert mail.outbox[1].subject.find('Welcome to') == 0
        assert u.username in mail.outbox[1].body


class ChangeEmailTestCase(TestCase):
    client_class = LocalizingClient

    def setUp(self):
        self.u = user(save=True)
        profile(user=self.u)
        self.client.login(username=self.u.username, password='testpass')
        super(ChangeEmailTestCase, self).setUp()

    def test_redirect(self):
        """Test our redirect from old url to new one."""
        response = self.client.get(reverse('users.old_change_email',
                                           locale='en-US'), follow=False)
        eq_(301, response.status_code)
        eq_('http://testserver/en-US/users/change_email', response['location'])

    @mock.patch.object(Site.objects, 'get_current')
    def test_user_change_email(self, get_current):
        """Send email to change user's email and then change it."""
        get_current.return_value.domain = 'su.mo.com'

        # Attempt to change email.
        response = self.client.post(reverse('users.change_email'),
                                    {'email': 'paulc@trololololololo.com'},
                                    follow=True)
        eq_(200, response.status_code)

        # Be notified to click a confirmation link.
        eq_(1, len(mail.outbox))
        assert mail.outbox[0].subject.find('Please confirm your') == 0
        ec = EmailChange.objects.all()[0]
        assert ec.activation_key in mail.outbox[0].body
        eq_('paulc@trololololololo.com', ec.email)

        # Visit confirmation link to change email.
        response = self.client.get(reverse('users.confirm_email',
                                           args=[ec.activation_key]))
        eq_(200, response.status_code)
        u = User.objects.get(username=self.u.username)
        eq_('paulc@trololololololo.com', u.email)

    def test_user_change_email_same(self):
        """Changing to same email shows validation error."""
        self.u.email = 'valid@email.com'
        self.u.save()
        response = self.client.post(reverse('users.change_email'),
                                    {'email': self.u.email})
        eq_(200, response.status_code)
        doc = pq(response.content)
        eq_('This is your current email.', doc('ul.errorlist').text())

    def test_user_change_email_duplicate(self):
        """Changing to same email shows validation error."""
        u = user(email='newvalid@email.com', save=True)
        response = self.client.post(reverse('users.change_email'),
                                    {'email': u.email})
        eq_(200, response.status_code)
        doc = pq(response.content)
        eq_('A user with that email address already exists.',
            doc('ul.errorlist').text())

    @mock.patch.object(Site.objects, 'get_current')
    def test_user_confirm_email_duplicate(self, get_current):
        """If we detect a duplicate email when confirming an email change,
        don't change it and notify the user."""
        get_current.return_value.domain = 'su.mo.com'
        old_email = self.u.email
        new_email = 'newvalid@email.com'
        response = self.client.post(reverse('users.change_email'),
                                    {'email': new_email})
        eq_(200, response.status_code)
        assert mail.outbox[0].subject.find('Please confirm your') == 0
        ec = EmailChange.objects.all()[0]

        # Before new email is confirmed, give the same email to a user
        u = user(email=new_email, save=True)

        # Visit confirmation link and verify email wasn't changed.
        response = self.client.get(reverse('users.confirm_email',
                                           args=[ec.activation_key]))
        eq_(200, response.status_code)
        doc = pq(response.content)
        eq_('Unable to change email for user %s' % self.u.username,
            doc('article h1').text())
        u = User.objects.get(username=self.u.username)
        eq_(old_email, u.email)


class AvatarTests(TestCase):
    def setUp(self):
        self.u = user(save=True)
        self.p = profile(user=self.u)
        self.client.login(username=self.u.username, password='testpass')
        super(AvatarTests, self).setUp()

    def tearDown(self):
        p = Profile.uncached.get(user=self.u)
        if os.path.exists(p.avatar.path):
            os.unlink(p.avatar.path)
        super(AvatarTests, self).tearDown()

    def test_upload_avatar(self):
        assert not self.p.avatar, 'User has no avatar.'
        with open('apps/upload/tests/media/test.jpg') as f:
            url = reverse('users.edit_avatar', locale='en-US')
            data = {'avatar': f}
            r = self.client.post(url, data)
        eq_(302, r.status_code)
        p = Profile.uncached.get(user=self.u)
        assert p.avatar, 'User has an avatar.'
        assert p.avatar.path.endswith('.png')

    def test_replace_missing_avatar(self):
        """If an avatar is missing, allow replacing it."""
        assert not self.p.avatar, 'User has no avatar.'
        self.p.avatar = 'path/does/not/exist.jpg'
        self.p.save()
        assert self.p.avatar, 'User has a bad avatar.'
        with open('apps/upload/tests/media/test.jpg') as f:
            url = reverse('users.edit_avatar', locale='en-US')
            data = {'avatar': f}
            r = self.client.post(url, data)
        eq_(302, r.status_code)
        p = Profile.uncached.get(user=self.u)
        assert p.avatar, 'User has an avatar.'
        assert not p.avatar.path.endswith('exist.jpg')
        assert p.avatar.path.endswith('.png')


class SessionTests(TestCase):
    client_class = LocalizingClient

    def setUp(self):
        self.u = user(save=True)
        self.client.logout()
        super(SessionTests, self).setUp()

    # Need to set DEBUG = True for @ssl_required to not freak out.
    @override_settings(DEBUG=True)
    def test_login_sets_extra_cookie(self):
        """On login, set the SESSION_EXISTS_COOKIE."""
        url = reverse('users.login')
        res = self.client.post(url, {'username': self.u.username,
                                     'password': 'testpass'})
        assert settings.SESSION_EXISTS_COOKIE in res.cookies
        c = res.cookies[settings.SESSION_EXISTS_COOKIE]
        assert 'secure' not in c.output().lower()

    @override_settings(DEBUG=True)
    def test_logout_deletes_cookie(self):
        """On logout, delete the SESSION_EXISTS_COOKIE."""
        url = reverse('users.logout')
        res = self.client.get(url)
        assert settings.SESSION_EXISTS_COOKIE in res.cookies
        c = res.cookies[settings.SESSION_EXISTS_COOKIE]
        assert '1970' in c['expires']

    @override_settings(DEBUG=True,
                       SESSION_EXPIRE_AT_BROWSER_CLOSE=True)
    def test_expire_at_browser_close(self):
        """If SESSION_EXPIRE_AT_BROWSER_CLOSE, do expire then."""
        url = reverse('users.login')
        res = self.client.post(url, {'username': self.u.username,
                                     'password': 'testpass'})
        c = res.cookies[settings.SESSION_EXISTS_COOKIE]
        eq_('', c['max-age'])

    @override_settings(DEBUG=True,
                       SESSION_EXPIRE_AT_BROWSER_CLOSE=False,
                       SESSION_COOKIE_AGE=123)
    def test_expire_in_a_long_time(self):
        """If not SESSION_EXPIRE_AT_BROWSER_CLOSE, set an expiry date."""
        url = reverse('users.login')
        res = self.client.post(url, {'username': self.u.username,
                                     'password': 'testpass'})
        c = res.cookies[settings.SESSION_EXISTS_COOKIE]
        eq_(123, c['max-age'])


class UserSettingsTests(TestCase):
    def setUp(self):
        self.u = user(save=True)
        self.p = profile(user=self.u)
        self.client.login(username=self.u.username, password='testpass')
        super(UserSettingsTests, self).setUp()

    def test_create_setting(self):
        url = reverse('users.edit_settings', locale='en-US')
        eq_(Setting.objects.filter(user=self.u).count(), 0)  # No settings
        res = self.client.get(url, follow=True)
        eq_(200, res.status_code)
        res = self.client.post(url, {'forums_watch_new_thread': True},
                               follow=True)
        eq_(200, res.status_code)
        assert Setting.get_for_user(self.u, 'forums_watch_new_thread')


class UserProfileTests(TestCase):
    def setUp(self):
        self.u = user(save=True)
        self.profile = profile(user=self.u)
        self.url = reverse('users.profile', args=[self.u.pk],
                           locale='en-US')
        super(UserProfileTests, self).setUp()

    def test_profile(self):
        res = self.client.get(self.url)
        self.assertContains(res, self.u.username)

    def test_profile_inactive(self):
        """Inactive users don't have a public profile."""
        self.u.is_active = False
        self.u.save()
        res = self.client.get(self.url)
        eq_(404, res.status_code)

    def test_profile_post(self):
        res = self.client.post(self.url)
        eq_(405, res.status_code)

    def test_profile_deactivate(self):
        """Test user deactivation"""
        p = profile()

        self.client.login(username=self.u.username, password='testpass')
        res = self.client.post(reverse('users.deactivate', locale='en-US'),
                               {'user_id': p.user.id})

        eq_(403, res.status_code)

        add_permission(self.u, Profile, 'deactivate_users')
        res = self.client.post(reverse('users.deactivate', locale='en-US'),
                               {'user_id': p.user.id})

        eq_(302, res.status_code)

        p = Profile.objects.get(user_id=p.user_id)
        assert not p.user.is_active
