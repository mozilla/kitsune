import os
from datetime import datetime, timedelta

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.core import mail
from django.test.utils import override_settings

import mock
from nose.tools import eq_
from pyquery import PyQuery as pq
from tidings.tests import watch

from kitsune.questions.tests import QuestionFactory, AnswerFactory
from kitsune.questions.models import Question, Answer
from kitsune.sumo.tests import (TestCase, LocalizingClient,
                                send_mail_raise_smtp)
from kitsune.sumo.urlresolvers import reverse
from kitsune.users import ERROR_SEND_EMAIL
from kitsune.users.models import (
    CONTRIBUTOR_GROUP, Profile, RegistrationProfile, EmailChange, Setting,
    email_utils, Deactivation)
from kitsune.users.tests import UserFactory, GroupFactory, add_permission


class RegisterTests(TestCase):
    def setUp(self):
        self.client.logout()
        super(RegisterTests, self).setUp()

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
        eq_('http://testserver/en-US/?fpa=1', response.redirect_chain[0][0])

    @mock.patch.object(email_utils, 'send_messages')
    @mock.patch.object(Site.objects, 'get_current')
    def test_new_user_smtp_error(self, get_current, send_messages):
        get_current.return_value.domain = 'su.mo.com'

        send_messages.side_effect = send_mail_raise_smtp
        response = self.client.post(
            reverse('users.registercontributor', locale='en-US'),
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
        eq_('http://testserver/ja/?fpa=1', response.redirect_chain[0][0])

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

        # Verify that the RegistrationProfile was nuked.
        eq_(0, RegistrationProfile.objects.filter(activation_key=key).count())

    @mock.patch.object(Site.objects, 'get_current')
    def test_question_created_time_on_user_activation(self, get_current):
        get_current.return_value.domain = 'su.mo.com'
        user_ = RegistrationProfile.objects.create_inactive_user(
            'sumouser1234', 'testpass', 'sumouser@test.com')
        assert not user_.is_active
        then = datetime.now() - timedelta(days=1)
        q = QuestionFactory(creator=user_, created=then)
        assert q.created == then
        key = RegistrationProfile.objects.all()[0].activation_key
        url = reverse('users.activate', args=[user_.id, key])
        response = self.client.get(url, follow=True)
        eq_(200, response.status_code)
        user_ = User.objects.get(pk=user_.pk)
        assert user_.is_active
        q = Question.objects.get(pk=q.pk)
        assert q.created > then

    @mock.patch.object(Site.objects, 'get_current')
    def test_new_user_claim_watches(self, get_current):
        """Claim user watches upon activation."""
        watch(email='sumouser@test.com', user=UserFactory(), save=True)

        get_current.return_value.domain = 'su.mo.com'
        user_ = RegistrationProfile.objects.create_inactive_user(
            'sumouser1234', 'testpass', 'sumouser@test.com')
        key = RegistrationProfile.objects.all()[0].activation_key
        self.client.get(reverse('users.activate', args=[user_.id, key]), follow=True)

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
        assert q.get_absolute_url().encode('utf8') in response.content

    def test_duplicate_username(self):
        u = UserFactory()
        response = self.client.post(
            reverse('users.registercontributor', locale='en-US'),
            {'username': u.username,
             'email': 'newbie@example.com',
             'password': 'foo',
             'password2': 'foo'}, follow=True)
        self.assertContains(response, 'already exists')

    def test_duplicate_email(self):
        u = UserFactory(email='noob@example.com')
        User.objects.create(username='noob', email='noob@example.com').save()
        response = self.client.post(
            reverse('users.registercontributor', locale='en-US'),
            {'username': 'newbie',
             'email': u.email,
             'password': 'foo',
             'password2': 'foo'}, follow=True)
        self.assertContains(response, 'already exists')

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
        GroupFactory(name=group_name)
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
        self.user = UserFactory()
        self.client.login(username=self.user.username, password='testpass')
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
        u = User.objects.get(username=self.user.username)
        eq_('paulc@trololololololo.com', u.email)

    def test_user_change_email_same(self):
        """Changing to same email shows validation error."""
        self.user.email = 'valid@email.com'
        self.user.save()
        response = self.client.post(reverse('users.change_email'),
                                    {'email': self.user.email})
        eq_(200, response.status_code)
        doc = pq(response.content)
        eq_('This is your current email.', doc('ul.errorlist').text())

    def test_user_change_email_duplicate(self):
        """Changing to same email shows validation error."""
        u = UserFactory(email='newvalid@email.com')
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
        old_email = self.user.email
        new_email = 'newvalid@email.com'
        response = self.client.post(reverse('users.change_email'),
                                    {'email': new_email})
        eq_(200, response.status_code)
        assert mail.outbox[0].subject.find('Please confirm your') == 0
        ec = EmailChange.objects.all()[0]

        # Before new email is confirmed, give the same email to a user
        u = UserFactory(email=new_email)

        # Visit confirmation link and verify email wasn't changed.
        response = self.client.get(reverse('users.confirm_email',
                                           args=[ec.activation_key]))
        eq_(200, response.status_code)
        doc = pq(response.content)
        eq_(u'Unable to change email for user %s' % self.user.username,
            doc('article h1').text())
        u = User.objects.get(username=self.user.username)
        eq_(old_email, u.email)


class MakeContributorTests(TestCase):
    def setUp(self):
        self.user = UserFactory()
        self.client.login(username=self.user.username, password='testpass')
        GroupFactory(name=CONTRIBUTOR_GROUP)
        super(MakeContributorTests, self).setUp()

    def test_make_contributor(self):
        """Test adding a user to the contributor group"""
        eq_(0, self.user.groups.filter(name=CONTRIBUTOR_GROUP).count())

        response = self.client.post(reverse('users.make_contributor',
                                            force_locale=True))
        eq_(302, response.status_code)

        eq_(1, self.user.groups.filter(name=CONTRIBUTOR_GROUP).count())


class AvatarTests(TestCase):
    def setUp(self):
        self.user = UserFactory()
        self.profile = self.user.profile
        self.client.login(username=self.user.username, password='testpass')
        super(AvatarTests, self).setUp()

    def tearDown(self):
        p = Profile.objects.get(user=self.user)
        if os.path.exists(p.avatar.path):
            os.unlink(p.avatar.path)
        super(AvatarTests, self).tearDown()

    def test_upload_avatar(self):
        assert not self.profile.avatar, 'User has no avatar.'
        with open('kitsune/upload/tests/media/test.jpg') as f:
            url = reverse('users.edit_avatar', locale='en-US')
            data = {'avatar': f}
            r = self.client.post(url, data)
        eq_(302, r.status_code)
        p = Profile.objects.get(user=self.user)
        assert p.avatar, 'User has an avatar.'
        assert p.avatar.path.endswith('.png')

    def test_replace_missing_avatar(self):
        """If an avatar is missing, allow replacing it."""
        assert not self.profile.avatar, 'User has no avatar.'
        self.profile.avatar = 'path/does/not/exist.jpg'
        self.profile.save()
        assert self.profile.avatar, 'User has a bad avatar.'
        with open('kitsune/upload/tests/media/test.jpg') as f:
            url = reverse('users.edit_avatar', locale='en-US')
            data = {'avatar': f}
            r = self.client.post(url, data)
        eq_(302, r.status_code)
        p = Profile.objects.get(user=self.user)
        assert p.avatar, 'User has an avatar.'
        assert not p.avatar.path.endswith('exist.jpg')
        assert p.avatar.path.endswith('.png')


class SessionTests(TestCase):
    client_class = LocalizingClient

    def setUp(self):
        self.user = UserFactory()
        self.client.logout()
        super(SessionTests, self).setUp()

    def test_login_sets_extra_cookie(self):
        """On login, set the SESSION_EXISTS_COOKIE."""
        url = reverse('users.login')
        res = self.client.post(url, {'username': self.user.username,
                                     'password': 'testpass'})
        assert settings.SESSION_EXISTS_COOKIE in res.cookies
        c = res.cookies[settings.SESSION_EXISTS_COOKIE]
        assert 'secure' not in c.output().lower()

    def test_logout_deletes_cookie(self):
        """On logout, delete the SESSION_EXISTS_COOKIE."""
        url = reverse('users.logout')
        res = self.client.post(url)
        assert settings.SESSION_EXISTS_COOKIE in res.cookies
        c = res.cookies[settings.SESSION_EXISTS_COOKIE]
        assert '1970' in c['expires']

    @override_settings(SESSION_EXPIRE_AT_BROWSER_CLOSE=True)
    def test_expire_at_browser_close(self):
        """If SESSION_EXPIRE_AT_BROWSER_CLOSE, do expire then."""
        url = reverse('users.login')
        res = self.client.post(url, {'username': self.user.username,
                                     'password': 'testpass'})
        c = res.cookies[settings.SESSION_EXISTS_COOKIE]
        eq_('', c['max-age'])

    @override_settings(SESSION_EXPIRE_AT_BROWSER_CLOSE=False,
                       SESSION_COOKIE_AGE=123)
    def test_expire_in_a_long_time(self):
        """If not SESSION_EXPIRE_AT_BROWSER_CLOSE, set an expiry date."""
        url = reverse('users.login')
        res = self.client.post(url, {'username': self.user.username,
                                     'password': 'testpass'})
        c = res.cookies[settings.SESSION_EXISTS_COOKIE]
        eq_(123, c['max-age'])


class UserSettingsTests(TestCase):
    def setUp(self):
        self.user = UserFactory()
        self.profile = self.user.profile
        self.client.login(username=self.user.username, password='testpass')
        super(UserSettingsTests, self).setUp()

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
        self.user = UserFactory()
        self.profile = self.user.profile
        self.userrl = reverse('users.profile', args=[self.user.username], locale='en-US')
        super(UserProfileTests, self).setUp()

    def test_ProfileFactory(self):
        res = self.client.get(self.userrl)
        self.assertContains(res, self.user.username)

    def test_profile_redirect(self):
        """Ensure that old profile URL's get redirected."""
        res = self.client.get(reverse('users.profile', args=[self.user.pk],
                                      locale='en-US'))
        eq_(302, res.status_code)

    def test_profile_inactive(self):
        """Inactive users don't have a public profile."""
        self.user.is_active = False
        self.user.save()
        res = self.client.get(self.userrl)
        eq_(404, res.status_code)

    def test_profile_post(self):
        res = self.client.post(self.userrl)
        eq_(405, res.status_code)

    def test_profile_deactivate(self):
        """Test user deactivation"""
        p = UserFactory().profile

        self.client.login(username=self.user.username, password='testpass')
        res = self.client.post(reverse('users.deactivate', locale='en-US'), {'user_id': p.user.id})

        eq_(403, res.status_code)

        add_permission(self.user, Profile, 'deactivate_users')
        res = self.client.post(reverse('users.deactivate', locale='en-US'), {'user_id': p.user.id})

        eq_(302, res.status_code)

        log = Deactivation.objects.get(user_id=p.user_id)
        eq_(log.moderator_id, self.user.id)

        p = Profile.objects.get(user_id=p.user_id)
        assert not p.user.is_active

    def test_deactivate_and_flag_spam(self):
        self.client.login(username=self.user.username, password='testpass')
        add_permission(self.user, Profile, 'deactivate_users')

        # Verify content is flagged as spam when requested.
        u = UserFactory()
        AnswerFactory(creator=u)
        QuestionFactory(creator=u)
        url = reverse('users.deactivate-spam', locale='en-US')
        res = self.client.post(url, {'user_id': u.id})

        eq_(302, res.status_code)
        eq_(1, Question.objects.filter(creator=u, is_spam=True).count())
        eq_(0, Question.objects.filter(creator=u, is_spam=False).count())
        eq_(1, Answer.objects.filter(creator=u, is_spam=True).count())
        eq_(0, Answer.objects.filter(creator=u, is_spam=False).count())
