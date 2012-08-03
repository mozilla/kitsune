import os

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.core import mail

import mock
from nose.tools import eq_
from pyquery import PyQuery as pq
from tidings.tests import watch

from questions.models import Question
from sumo.tests import TestCase, LocalizingClient, send_mail_raise_smtp
from sumo.urlresolvers import reverse
from users import ERROR_SEND_EMAIL
from users.models import Profile, RegistrationProfile, EmailChange, Setting
from users.tests import profile, user, group


class RegisterTests(TestCase):
    fixtures = ['users.json']

    def setUp(self):
        self.old_debug = settings.DEBUG
        settings.DEBUG = True
        self.client.logout()

    def tearDown(self):
        settings.DEBUG = self.old_debug

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
        eq_('http://testserver/en-US/home', response.redirect_chain[0][0])

    @mock.patch.object(mail, 'send_mail')
    @mock.patch.object(Site.objects, 'get_current')
    def test_new_user_smtp_error(self, get_current, send_mail):
        get_current.return_value.domain = 'su.mo.com'

        send_mail.side_effect = send_mail_raise_smtp
        response = self.client.post(reverse('users.register', locale='en-US'),
                                    {'username': 'newbie',
                                     'email': 'newbie@example.com',
                                     'password': 'foobar22',
                                     'password2': 'foobar22'}, follow=True)
        self.assertContains(response, unicode(ERROR_SEND_EMAIL))
        assert not User.objects.filter(username='newbie').exists()

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
        eq_('http://testserver/ja/home', response.redirect_chain[0][0])

    @mock.patch.object(Site.objects, 'get_current')
    def test_new_user_activation(self, get_current):
        get_current.return_value.domain = 'su.mo.com'
        user = RegistrationProfile.objects.create_inactive_user(
            'sumouser1234', 'testpass', 'sumouser@test.com')
        assert not user.is_active
        key = RegistrationProfile.objects.all()[0].activation_key
        url = reverse('users.activate', args=[user.id, key])
        response = self.client.get(url, follow=True)
        eq_(200, response.status_code)
        user = User.objects.get(pk=user.pk)
        assert user.is_active

    @mock.patch.object(Site.objects, 'get_current')
    def test_new_user_claim_watches(self, get_current):
        """Claim user watches upon activation."""
        watch(email='sumouser@test.com', save=True)

        get_current.return_value.domain = 'su.mo.com'
        user = RegistrationProfile.objects.create_inactive_user(
            'sumouser1234', 'testpass', 'sumouser@test.com')
        key = RegistrationProfile.objects.all()[0].activation_key
        self.client.get(reverse('users.activate', args=[user.id, key]),
                        follow=True)

        # Watches are claimed.
        assert user.watch_set.exists()

    @mock.patch.object(Site.objects, 'get_current')
    def test_new_user_with_questions(self, get_current):
        """The user's questions are mentioned on the confirmation page."""
        get_current.return_value.domain = 'su.mo.com'
        # TODO: remove this test once we drop unconfirmed questions.
        user = RegistrationProfile.objects.create_inactive_user(
            'sumouser1234', 'testpass', 'sumouser@test.com')

        # Before we activate, let's create a question.
        q = Question.objects.create(title='test_question', creator=user,
                                    content='test')

        # Activate account.
        key = RegistrationProfile.objects.all()[0].activation_key
        url = reverse('users.activate', args=[user.id, key])
        response = self.client.get(url, follow=True)
        eq_(200, response.status_code)

        q = Question.objects.get(creator=user)
        # Question is listed on the confirmation page.
        assert 'test_question' in response.content
        assert q.get_absolute_url() in response.content

    def test_duplicate_username(self):
        response = self.client.post(reverse('users.register', locale='en-US'),
                                    {'username': 'jsocol',
                                     'email': 'newbie@example.com',
                                     'password': 'foo',
                                     'password2': 'foo'}, follow=True)
        self.assertContains(response, 'already exists')

    def test_duplicate_email(self):
        User.objects.create(username='noob', email='noob@example.com').save()
        response = self.client.post(reverse('users.register', locale='en-US'),
                                    {'username': 'newbie',
                                     'email': 'noob@example.com',
                                     'password': 'foo',
                                     'password2': 'foo'}, follow=True)
        self.assertContains(response, 'already exists')

    def test_no_match_passwords(self):
        response = self.client.post(reverse('users.register', locale='en-US'),
                                    {'username': 'newbie',
                                     'email': 'newbie@example.com',
                                     'password': 'foo',
                                     'password2': 'bar'}, follow=True)
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


class ChangeEmailTestCase(TestCase):
    fixtures = ['users.json']
    client_class = LocalizingClient

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

        self.client.login(username='pcraciunoiu', password='testpass')
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
        u = User.objects.get(username='pcraciunoiu')
        eq_('paulc@trololololololo.com', u.email)

    def test_user_change_email_same(self):
        """Changing to same email shows validation error."""
        self.client.login(username='rrosario', password='testpass')
        user = User.objects.get(username='rrosario')
        user.email = 'valid@email.com'
        user.save()
        response = self.client.post(reverse('users.change_email'),
                                    {'email': user.email})
        eq_(200, response.status_code)
        doc = pq(response.content)
        eq_('This is your current email.', doc('ul.errorlist').text())

    def test_user_change_email_duplicate(self):
        """Changing to same email shows validation error."""
        self.client.login(username='rrosario', password='testpass')
        email = 'newvalid@email.com'
        User.objects.filter(username='pcraciunoiu').update(email=email)
        response = self.client.post(reverse('users.change_email'),
                                    {'email': email})
        eq_(200, response.status_code)
        doc = pq(response.content)
        eq_('A user with that email address already exists.',
            doc('ul.errorlist').text())

    @mock.patch.object(Site.objects, 'get_current')
    def test_user_confirm_email_duplicate(self, get_current):
        """If we detect a duplicate email when confirming an email change,
        don't change it and notify the user."""
        get_current.return_value.domain = 'su.mo.com'
        self.client.login(username='rrosario', password='testpass')
        old_email = User.objects.get(username='rrosario').email
        new_email = 'newvalid@email.com'
        response = self.client.post(reverse('users.change_email'),
                                    {'email': new_email})
        eq_(200, response.status_code)
        assert mail.outbox[0].subject.find('Please confirm your') == 0
        ec = EmailChange.objects.all()[0]

        # Before new email is confirmed, give the same email to a user
        User.objects.filter(username='pcraciunoiu').update(email=new_email)

        # Visit confirmation link and verify email wasn't changed.
        response = self.client.get(reverse('users.confirm_email',
                                           args=[ec.activation_key]))
        eq_(200, response.status_code)
        doc = pq(response.content)
        eq_('Unable to change email for user rrosario',
            doc('#main h1').text())
        u = User.objects.get(username='rrosario')
        eq_(old_email, u.email)


class AvatarTests(TestCase):
    def setUp(self):
        self.u = user()
        self.u.save()
        self.p = profile(user=self.u)
        self.client.login(username=self.u.username, password='testpass')

    def tearDown(self):
        p = Profile.uncached.get(user=self.u)
        if os.path.exists(p.avatar.path):
            os.unlink(p.avatar.path)

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
        self.u = user()
        self.u.save()
        self.client.logout()

    # Need to set DEBUG = True for @ssl_required to not freak out.
    @mock.patch.object(settings._wrapped, 'DEBUG', True)
    def test_login_sets_extra_cookie(self):
        """On login, set the SESSION_EXISTS_COOKIE."""
        url = reverse('users.login')
        res = self.client.post(url, {'username': self.u.username,
                                     'password': 'testpass'})
        assert settings.SESSION_EXISTS_COOKIE in res.cookies
        c = res.cookies[settings.SESSION_EXISTS_COOKIE]
        assert 'secure' not in c.output().lower()

    @mock.patch.object(settings._wrapped, 'DEBUG', True)
    def test_logout_deletes_cookie(self):
        """On logout, delete the SESSION_EXISTS_COOKIE."""
        url = reverse('users.logout')
        res = self.client.get(url)
        assert settings.SESSION_EXISTS_COOKIE in res.cookies
        c = res.cookies[settings.SESSION_EXISTS_COOKIE]
        assert '1970' in c['expires']

    @mock.patch.object(settings._wrapped, 'DEBUG', True, create=True)
    @mock.patch.object(settings._wrapped, 'SESSION_EXPIRE_AT_BROWSER_CLOSE',
                       True, create=True)
    def test_expire_at_browser_close(self):
        """If SESSION_EXPIRE_AT_BROWSER_CLOSE, do expire then."""
        url = reverse('users.login')
        res = self.client.post(url, {'username': self.u.username,
                                     'password': 'testpass'})
        c = res.cookies[settings.SESSION_EXISTS_COOKIE]
        eq_('', c['max-age'])

    @mock.patch.object(settings._wrapped, 'DEBUG', True, create=True)
    @mock.patch.object(settings._wrapped, 'SESSION_EXPIRE_AT_BROWSER_CLOSE',
                       False, create=True)
    @mock.patch.object(settings._wrapped, 'SESSION_COOKIE_AGE', 123,
                       create=True)
    def test_expire_in_a_long_time(self):
        """If not SESSION_EXPIRE_AT_BROWSER_CLOSE, set an expiry date."""
        url = reverse('users.login')
        res = self.client.post(url, {'username': self.u.username,
                                     'password': 'testpass'})
        c = res.cookies[settings.SESSION_EXISTS_COOKIE]
        eq_(123, c['max-age'])


class UserSettingsTests(TestCase):
    def setUp(self):
        self.user = user()
        self.user.save()
        self.p = profile(user=self.user)
        self.client.login(username=self.user.username, password='testpass')

    def test_create_setting(self):
        url = reverse('users.edit_settings', locale='en-US')
        eq_(Setting.objects.filter(user=self.user).count(), 0)  # No settings
        res = self.client.get(url, follow=True)
        eq_(200, res.status_code)
        res = self.client.post(url, {'forums_watch_new_thread': True},
                               follow=True)
        eq_(200, res.status_code)
        assert Setting.get_for_user(self.user, 'forums_watch_new_thread')


class UserProfileTests(TestCase):
    def setUp(self):
        self.user = user()
        self.user.save()
        self.profile = profile(user=self.user)
        self.url = reverse('users.profile', args=[self.user.pk],
                           locale='en-US')

    def test_profile(self):
        res = self.client.get(self.url)
        self.assertContains(res, self.user.username)

    def test_profile_inactive(self):
        """Inactive users don't have a public profile."""
        self.user.is_active = False
        self.user.save()
        res = self.client.get(self.url)
        eq_(404, res.status_code)

    def test_profile_post(self):
        res = self.client.post(self.url)
        eq_(405, res.status_code)
