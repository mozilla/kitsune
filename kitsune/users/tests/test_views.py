
from django.contrib import messages
from django.contrib.messages.middleware import MessageMiddleware
from django.contrib.sessions.middleware import SessionMiddleware
from django.test.client import RequestFactory
from nose.tools import eq_
from pyquery import PyQuery as pq

from kitsune.questions.models import Answer, Question
from kitsune.questions.tests import AnswerFactory, QuestionFactory
from kitsune.sumo.tests import LocalizingClient, TestCase
from kitsune.sumo.urlresolvers import reverse
from kitsune.users.models import (CONTRIBUTOR_GROUP, Deactivation, Profile,
                                  Setting)
from kitsune.users.tests import GroupFactory, UserFactory, add_permission
from kitsune.users.views import edit_profile


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


class ProfileNotificationTests(TestCase):
    """
    These tests confirm that FXA and non-FXA messages render properly.
    We use RequestFactory because the request object from self.client.request
    cannot be passed into messages.info()
    """
    def _get_request(self):
        user = UserFactory()
        request = RequestFactory().get(reverse('users.edit_profile', args=[user.username]))
        request.user = user
        request.LANGUAGE_CODE = 'en'

        middleware = SessionMiddleware()
        middleware.process_request(request)
        request.session.save()

        middleware = MessageMiddleware()
        middleware.process_request(request)
        request.session.save()
        return request

    def test_fxa_notification_updated(self):
        request = self._get_request()
        messages.info(request, 'fxa_notification_updated')
        response = edit_profile(request)
        doc = pq(response.content)
        eq_(1, len(doc('#fxa-notification-updated')))
        eq_(0, len(doc('#fxa-notification-created')))

    def test_fxa_notification_created(self):
        request = self._get_request()
        messages.info(request, 'fxa_notification_created')
        response = edit_profile(request)
        doc = pq(response.content)
        eq_(0, len(doc('#fxa-notification-updated')))
        eq_(1, len(doc('#fxa-notification-created')))

    def test_non_fxa_notification_created(self):
        request = self._get_request()
        text = 'This is a helpful piece of information'
        messages.info(request, text)
        response = edit_profile(request)
        doc = pq(response.content)
        eq_(0, len(doc('#fxa-notification-updated')))
        eq_(0, len(doc('#fxa-notification-created')))
        eq_(1, len(doc('.user-messages li')))
        eq_(doc('.user-messages li').text(), text)


class FXAAuthenticationTests(TestCase):
    client_class = LocalizingClient

    def test_authenticate_does_not_update_session(self):
        self.client.get(reverse('users.fxa_authentication_init'))
        assert not self.client.session.get('is_contributor')

    def test_authenticate_does_update_session(self):
        url = reverse('users.fxa_authentication_init') + '?is_contributor=True'
        self.client.get(url)
        assert self.client.session.get('is_contributor')
