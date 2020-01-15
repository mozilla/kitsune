import os

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib.messages.middleware import MessageMiddleware
from django.contrib.sites.models import Site
from django.core import mail
from django.test.client import RequestFactory
from django.test.utils import override_settings


import mock
from nose.tools import eq_
from pyquery import PyQuery as pq

from kitsune.questions.tests import QuestionFactory, AnswerFactory
from kitsune.questions.models import Question, Answer
from kitsune.sumo.tests import TestCase, LocalizingClient
from kitsune.sumo.urlresolvers import reverse
from kitsune.users.models import (
    CONTRIBUTOR_GROUP,
    Profile,
    EmailChange,
    Setting,
    Deactivation,
)
from kitsune.users.tests import UserFactory, GroupFactory, add_permission
from kitsune.users.views import edit_profile


class LoginTests(TestCase):
    @mock.patch.object(Site.objects, "get_current")
    def test_fxa_migrated_user_cannot_login_with_sumo(self, get_current):
        """
        If a user's profile is_fxa_migrated, then they cannot log in using
        the SUMO form. They should not be authenticated and they should
        see a notification error
        """
        user = UserFactory(password="1234")
        user.profile.is_fxa_migrated = True
        user.profile.save()
        response = self.client.post(
            reverse("users.login", locale="en-US"),
            {"username": user.username, "password": "1234"},
            follow=True,
        )

        assert not response.wsgi_request.user.is_authenticated()
        assert pq(response.content).find("#fxa-notification-already-migrated")


class ChangeEmailTestCase(TestCase):
    client_class = LocalizingClient

    def setUp(self):
        self.user = UserFactory()
        self.client.login(username=self.user.username, password="testpass")
        super(ChangeEmailTestCase, self).setUp()

    def test_redirect(self):
        """Test our redirect from old url to new one."""
        response = self.client.get(
            reverse("users.old_change_email", locale="en-US"), follow=False
        )
        eq_(301, response.status_code)
        eq_("/en-US/users/change_email", response["location"])

    @mock.patch.object(Site.objects, "get_current")
    def test_user_change_email(self, get_current):
        """Send email to change user's email and then change it."""
        get_current.return_value.domain = "su.mo.com"

        # Attempt to change email.
        response = self.client.post(
            reverse("users.change_email"),
            {"email": "paulc@trololololololo.com"},
            follow=True,
        )
        eq_(200, response.status_code)

        # Be notified to click a confirmation link.
        eq_(1, len(mail.outbox))
        assert mail.outbox[0].subject.find("Please confirm your") == 0
        ec = EmailChange.objects.all()[0]
        assert ec.activation_key in mail.outbox[0].body
        eq_("paulc@trololololololo.com", ec.email)

        # Visit confirmation link to change email.
        response = self.client.get(
            reverse("users.confirm_email", args=[ec.activation_key])
        )
        eq_(200, response.status_code)
        u = User.objects.get(username=self.user.username)
        eq_("paulc@trololololololo.com", u.email)

    def test_user_change_email_same(self):
        """Changing to same email shows validation error."""
        self.user.email = "valid@email.com"
        self.user.save()
        response = self.client.post(
            reverse("users.change_email"), {"email": self.user.email}
        )
        eq_(200, response.status_code)
        doc = pq(response.content)
        eq_("This is your current email.", doc("ul.errorlist").text())

    def test_user_change_email_duplicate(self):
        """Changing to same email shows validation error."""
        u = UserFactory(email="newvalid@email.com")
        response = self.client.post(reverse("users.change_email"), {"email": u.email})
        eq_(200, response.status_code)
        doc = pq(response.content)
        eq_(
            "A user with that email address already exists.", doc("ul.errorlist").text()
        )

    @mock.patch.object(Site.objects, "get_current")
    def test_user_confirm_email_duplicate(self, get_current):
        """If we detect a duplicate email when confirming an email change,
        don't change it and notify the user."""
        get_current.return_value.domain = "su.mo.com"
        old_email = self.user.email
        new_email = "newvalid@email.com"
        response = self.client.post(reverse("users.change_email"), {"email": new_email})
        eq_(200, response.status_code)
        assert mail.outbox[0].subject.find("Please confirm your") == 0
        ec = EmailChange.objects.all()[0]

        # Before new email is confirmed, give the same email to a user
        u = UserFactory(email=new_email)

        # Visit confirmation link and verify email wasn't changed.
        response = self.client.get(
            reverse("users.confirm_email", args=[ec.activation_key])
        )
        eq_(200, response.status_code)
        doc = pq(response.content)
        eq_(
            u"Unable to change email for user %s" % self.user.username,
            doc("article h1").text(),
        )
        u = User.objects.get(username=self.user.username)
        eq_(old_email, u.email)


class MakeContributorTests(TestCase):
    def setUp(self):
        self.user = UserFactory()
        self.client.login(username=self.user.username, password="testpass")
        GroupFactory(name=CONTRIBUTOR_GROUP)
        super(MakeContributorTests, self).setUp()

    def test_make_contributor(self):
        """Test adding a user to the contributor group"""
        eq_(0, self.user.groups.filter(name=CONTRIBUTOR_GROUP).count())

        response = self.client.post(
            reverse("users.make_contributor", force_locale=True)
        )
        eq_(302, response.status_code)

        eq_(1, self.user.groups.filter(name=CONTRIBUTOR_GROUP).count())


class AvatarTests(TestCase):
    def setUp(self):
        self.user = UserFactory()
        self.profile = self.user.profile
        self.client.login(username=self.user.username, password="testpass")
        super(AvatarTests, self).setUp()

    def tearDown(self):
        p = Profile.objects.get(user=self.user)
        if os.path.exists(p.avatar.path):
            os.unlink(p.avatar.path)
        super(AvatarTests, self).tearDown()

    def test_upload_avatar(self):
        assert not self.profile.avatar, "User has no avatar."
        with open("kitsune/upload/tests/media/test.jpg") as f:
            url = reverse("users.edit_avatar", locale="en-US")
            data = {"avatar": f}
            r = self.client.post(url, data)
        eq_(302, r.status_code)
        p = Profile.objects.get(user=self.user)
        assert p.avatar, "User has an avatar."
        assert p.avatar.path.endswith(".png")

    def test_replace_missing_avatar(self):
        """If an avatar is missing, allow replacing it."""
        assert not self.profile.avatar, "User has no avatar."
        self.profile.avatar = "path/does/not/exist.jpg"
        self.profile.save()
        assert self.profile.avatar, "User has a bad avatar."
        with open("kitsune/upload/tests/media/test.jpg") as f:
            url = reverse("users.edit_avatar", locale="en-US")
            data = {"avatar": f}
            r = self.client.post(url, data)
        eq_(302, r.status_code)
        p = Profile.objects.get(user=self.user)
        assert p.avatar, "User has an avatar."
        assert not p.avatar.path.endswith("exist.jpg")
        assert p.avatar.path.endswith(".png")


class SessionTests(TestCase):
    client_class = LocalizingClient

    def setUp(self):
        self.user = UserFactory()
        self.client.logout()
        super(SessionTests, self).setUp()

    def test_login_sets_extra_cookie(self):
        """On login, set the SESSION_EXISTS_COOKIE."""
        url = reverse("users.login")
        res = self.client.post(
            url, {"username": self.user.username, "password": "testpass"}
        )
        assert settings.SESSION_EXISTS_COOKIE in res.cookies
        c = res.cookies[settings.SESSION_EXISTS_COOKIE]
        assert "secure" not in c.output().lower()

    def test_logout_deletes_cookie(self):
        """On logout, delete the SESSION_EXISTS_COOKIE."""
        url = reverse("users.logout")
        res = self.client.post(url)
        assert settings.SESSION_EXISTS_COOKIE in res.cookies
        c = res.cookies[settings.SESSION_EXISTS_COOKIE]
        assert "1970" in c["expires"]

    @override_settings(SESSION_EXPIRE_AT_BROWSER_CLOSE=True)
    def test_expire_at_browser_close(self):
        """If SESSION_EXPIRE_AT_BROWSER_CLOSE, do expire then."""
        url = reverse("users.login")
        res = self.client.post(
            url, {"username": self.user.username, "password": "testpass"}
        )
        c = res.cookies[settings.SESSION_EXISTS_COOKIE]
        eq_("", c["max-age"])

    @override_settings(SESSION_EXPIRE_AT_BROWSER_CLOSE=False, SESSION_COOKIE_AGE=123)
    def test_expire_in_a_long_time(self):
        """If not SESSION_EXPIRE_AT_BROWSER_CLOSE, set an expiry date."""
        url = reverse("users.login")
        res = self.client.post(
            url, {"username": self.user.username, "password": "testpass"}
        )
        c = res.cookies[settings.SESSION_EXISTS_COOKIE]
        eq_(123, c["max-age"])

    def test_fxa_login_deletes_cookie(self):
        """
        If an FXA successfully authenticates using their SUMO credentials,
        we immediately log them out and clear their cookies, as they
        should only be authenticating via FXA
        """
        url = reverse("users.login")
        self.user.profile.is_fxa_migrated = True
        self.user.profile.save()
        res = self.client.post(
            url, {"username": self.user.username, "password": "testpass"}
        )
        session_cookie = res.cookies[settings.SESSION_EXISTS_COOKIE]
        assert "1970" in session_cookie["expires"]


class UserSettingsTests(TestCase):
    def setUp(self):
        self.user = UserFactory()
        self.profile = self.user.profile
        self.client.login(username=self.user.username, password="testpass")
        super(UserSettingsTests, self).setUp()

    def test_create_setting(self):
        url = reverse("users.edit_settings", locale="en-US")
        eq_(Setting.objects.filter(user=self.user).count(), 0)  # No settings
        res = self.client.get(url, follow=True)
        eq_(200, res.status_code)
        res = self.client.post(url, {"forums_watch_new_thread": True}, follow=True)
        eq_(200, res.status_code)
        assert Setting.get_for_user(self.user, "forums_watch_new_thread")


class UserProfileTests(TestCase):
    def setUp(self):
        self.user = UserFactory()
        self.profile = self.user.profile
        self.userrl = reverse(
            "users.profile", args=[self.user.username], locale="en-US"
        )
        super(UserProfileTests, self).setUp()

    def test_ProfileFactory(self):
        res = self.client.get(self.userrl)
        self.assertContains(res, self.user.username)

    def test_profile_redirect(self):
        """Ensure that old profile URL's get redirected."""
        res = self.client.get(
            reverse("users.profile", args=[self.user.pk], locale="en-US")
        )
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

        self.client.login(username=self.user.username, password="testpass")
        res = self.client.post(
            reverse("users.deactivate", locale="en-US"), {"user_id": p.user.id}
        )

        eq_(403, res.status_code)

        add_permission(self.user, Profile, "deactivate_users")
        res = self.client.post(
            reverse("users.deactivate", locale="en-US"), {"user_id": p.user.id}
        )

        eq_(302, res.status_code)

        log = Deactivation.objects.get(user_id=p.user_id)
        eq_(log.moderator_id, self.user.id)

        p = Profile.objects.get(user_id=p.user_id)
        assert not p.user.is_active

    def test_deactivate_and_flag_spam(self):
        self.client.login(username=self.user.username, password="testpass")
        add_permission(self.user, Profile, "deactivate_users")

        # Verify content is flagged as spam when requested.
        u = UserFactory()
        AnswerFactory(creator=u)
        QuestionFactory(creator=u)
        url = reverse("users.deactivate-spam", locale="en-US")
        res = self.client.post(url, {"user_id": u.id})

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
        request = RequestFactory().get(
            reverse("users.edit_profile", args=[user.username])
        )
        request.user = user
        request.MOBILE = False
        request.LANGUAGE_CODE = "en"
        request.META = {}

        middleware = SessionMiddleware()
        middleware.process_request(request)
        request.session.save()

        middleware = MessageMiddleware()
        middleware.process_request(request)
        request.session.save()
        return request

    def test_fxa_notification_updated(self):
        request = self._get_request()
        messages.info(request, "fxa_notification_updated")
        response = edit_profile(request)
        doc = pq(response.content)
        eq_(1, len(doc("#fxa-notification-updated")))
        eq_(0, len(doc("#fxa-notification-created")))

    def test_fxa_notification_created(self):
        request = self._get_request()
        messages.info(request, "fxa_notification_created")
        response = edit_profile(request)
        doc = pq(response.content)
        eq_(0, len(doc("#fxa-notification-updated")))
        eq_(1, len(doc("#fxa-notification-created")))

    def test_non_fxa_notification_created(self):
        request = self._get_request()
        text = "This is a helpful piece of information"
        messages.info(request, text)
        response = edit_profile(request)
        doc = pq(response.content)
        eq_(0, len(doc("#fxa-notification-updated")))
        eq_(0, len(doc("#fxa-notification-created")))
        eq_(1, len(doc(".user-messages li")))
        eq_(doc(".user-messages li").text(), text)


class FXAAuthenticationTests(TestCase):
    client_class = LocalizingClient

    def test_authenticate_does_not_update_session(self):
        self.client.get(reverse("users.fxa_authentication_init"))
        assert not self.client.session.get("is_contributor")

    def test_authenticate_does_update_session(self):
        url = reverse("users.fxa_authentication_init") + "?is_contributor=True"
        self.client.get(url)
        assert self.client.session.get("is_contributor")
