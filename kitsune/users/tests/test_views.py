import json
from functools import wraps
from textwrap import dedent
from unittest import mock

from django.contrib import messages
from django.contrib.messages.middleware import MessageMiddleware
from django.contrib.sessions.middleware import SessionMiddleware
from django.test.client import RequestFactory
from django.test.utils import override_settings
from josepy import jwa
from josepy import jwk
from josepy import jws
from nose.tools import eq_
from pyquery import PyQuery as pq

from kitsune.questions.models import Answer
from kitsune.questions.models import Question
from kitsune.questions.tests import AnswerFactory
from kitsune.questions.tests import QuestionFactory
from kitsune.sumo.tests import LocalizingClient
from kitsune.sumo.tests import TestCase
from kitsune.sumo.urlresolvers import reverse
from kitsune.users.models import AccountEvent
from kitsune.users.models import CONTRIBUTOR_GROUP
from kitsune.users.models import Deactivation
from kitsune.users.models import Profile
from kitsune.users.models import Setting
from kitsune.users.tests import add_permission
from kitsune.users.tests import GroupFactory
from kitsune.users.tests import ProfileFactory
from kitsune.users.tests import UserFactory
from kitsune.users.views import edit_profile


class MakeContributorTests(TestCase):
    def setUp(self):
        self.user = UserFactory()
        self.client.login(username=self.user.username, password="testpass")
        GroupFactory(name=CONTRIBUTOR_GROUP)
        super(MakeContributorTests, self).setUp()

    def test_make_contributor(self):
        """Test adding a user to the contributor group"""
        eq_(0, self.user.groups.filter(name=CONTRIBUTOR_GROUP).count())

        response = self.client.post(reverse("users.make_contributor", force_locale=True))
        eq_(302, response.status_code)

        eq_(1, self.user.groups.filter(name=CONTRIBUTOR_GROUP).count())


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
        self.userrl = reverse("users.profile", args=[self.user.username], locale="en-US")
        super(UserProfileTests, self).setUp()

    def test_ProfileFactory(self):
        res = self.client.get(self.userrl)
        self.assertContains(res, self.user.username)

    def test_profile_redirect(self):
        """Ensure that old profile URL's get redirected."""
        res = self.client.get(reverse("users.profile", args=[self.user.pk], locale="en-US"))
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
        res = self.client.post(reverse("users.deactivate", locale="en-US"), {"user_id": p.user.id})

        eq_(403, res.status_code)

        add_permission(self.user, Profile, "deactivate_users")
        res = self.client.post(reverse("users.deactivate", locale="en-US"), {"user_id": p.user.id})

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
        request = RequestFactory().get(reverse("users.edit_profile", args=[user.username]))
        request.user = user
        request.LANGUAGE_CODE = "en"

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


def setup_key(test):
    @wraps(test)
    def wrapper(self, *args, **kwargs):
        with mock.patch("kitsune.users.views.requests") as mock_requests:
            pem = dedent(
                """
            -----BEGIN RSA PRIVATE KEY-----
            MIIBOgIBAAJBAKx1c7RR7R/drnBSQ/zfx1vQLHUbFLh1AQQQ5R8DZUXd36efNK79
            vukFhN9HFoHZiUvOjm0c+pVE6K+EdE/twuUCAwEAAQJAMbrEnJCrQe8YqAbw1/Bn
            elAzIamndfE3U8bTavf9sgFpS4HL83rhd6PDbvx81ucaJAT/5x048fM/nFl4fzAc
            mQIhAOF/a9o3EIsDKEmUl+Z1OaOiUxDF3kqWSmALEsmvDhwXAiEAw8ljV5RO/rUp
            Zu2YMDFq3MKpyyMgBIJ8CxmGRc6gCmMCIGRQzkcmhfqBrhOFwkmozrqIBRIKJIjj
            8TRm2LXWZZ2DAiAqVO7PztdNpynugUy4jtbGKKjBrTSNBRGA7OHlUgm0dQIhALQq
            6oGU29Vxlvt3k0vmiRKU4AVfLyNXIGtcWcNG46h/
            -----END RSA PRIVATE KEY-----
            """
            )
            key = jwk.JWKRSA.load(pem.encode())
            pubkey = {"kty": "RSA", "alg": "RS256", "kid": "123"}
            pubkey.update(key.public_key().fields_to_partial_json())

            mock_json = mock.Mock()
            mock_json.json.return_value = {"keys": [pubkey]}
            mock_requests.get.return_value = mock_json
            test(self, key, *args, **kwargs)

    return wrapper


@override_settings(FXA_RP_CLIENT_ID="12345")
@override_settings(FXA_SET_ISSUER="http://example.com")
class WebhookViewTests(TestCase):
    def _call_webhook(self, events, key=None):
        payload = json.dumps(
            {
                "iss": "http://example.com",
                "sub": "54321",
                "aud": "12345",
                "iat": 1565720808,
                "jti": "e19ed6c5-4816-4171-aa43-56ffe80dbda1",
                "events": events,
            }
        )
        jwt = jws.JWS.sign(
            payload=payload.encode(),
            key=key,
            alg=jwa.RS256,
            kid="123",
            protect=frozenset(["alg", "kid"]),
        ).to_compact()
        return self.client.post(
            reverse("users.fxa_webhook"),
            content_type="",
            HTTP_AUTHORIZATION="Bearer " + jwt.decode(),
        )

    @mock.patch("kitsune.users.views.process_event_password_change")
    @setup_key
    def test_adds_event_to_db(self, key, process_mock):
        profile = ProfileFactory(fxa_uid="54321")
        events = {
            "https://schemas.accounts.firefox.com/event/password-change": {
                "changeTime": 1565721242227
            }
        }

        eq_(0, AccountEvent.objects.count())

        response = self._call_webhook(events, key)

        eq_(202, response.status_code)
        eq_(1, AccountEvent.objects.count())
        eq_(1, process_mock.delay.call_count)

        account_event = AccountEvent.objects.last()
        eq_(account_event.status, AccountEvent.UNPROCESSED)
        self.assertEqual(json.loads(account_event.body), list(events.values())[0])
        eq_(account_event.event_type, AccountEvent.PASSWORD_CHANGE)
        eq_(account_event.fxa_uid, "54321")
        eq_(account_event.jwt_id, "e19ed6c5-4816-4171-aa43-56ffe80dbda1")
        eq_(account_event.issued_at, "1565720808")
        eq_(account_event.profile, profile)

    @mock.patch("kitsune.users.views.process_event_subscription_state_change")
    @setup_key
    def test_adds_multiple_events_to_db(self, key, process_mock):
        profile = ProfileFactory(fxa_uid="54321")
        events = {
            "https://schemas.accounts.firefox.com/event/profile-change": {},
            "https://schemas.accounts.firefox.com/event/subscription-state-change": {
                "capabilities": ["capability_1", "capability_2"],
                "isActive": True,
                "changeTime": 1565721242227,
            },
        }

        eq_(0, AccountEvent.objects.count())

        response = self._call_webhook(events, key)

        eq_(202, response.status_code)
        eq_(2, AccountEvent.objects.count())
        eq_(1, process_mock.delay.call_count)

        account_event_1 = AccountEvent.objects.get(event_type=AccountEvent.PROFILE_CHANGE)
        account_event_2 = AccountEvent.objects.get(
            event_type=AccountEvent.SUBSCRIPTION_STATE_CHANGE
        )

        self.assertEqual(json.loads(account_event_1.body), {})
        self.assertEqual(json.loads(account_event_2.body), list(events.values())[1])

        eq_(account_event_1.status, AccountEvent.NOT_IMPLEMENTED)
        eq_(account_event_2.status, AccountEvent.UNPROCESSED)
        eq_(account_event_1.fxa_uid, "54321")
        eq_(account_event_2.fxa_uid, "54321")
        eq_(account_event_1.jwt_id, "e19ed6c5-4816-4171-aa43-56ffe80dbda1")
        eq_(account_event_2.jwt_id, "e19ed6c5-4816-4171-aa43-56ffe80dbda1")
        eq_(account_event_1.issued_at, "1565720808")
        eq_(account_event_2.issued_at, "1565720808")
        eq_(account_event_1.profile, profile)
        eq_(account_event_2.profile, profile)

    @mock.patch("kitsune.users.views.process_event_delete_user")
    @setup_key
    def test_handles_unknown_events(self, key, process_mock):
        profile = ProfileFactory(fxa_uid="54321")
        events = {
            "https://schemas.accounts.firefox.com/event/delete-user": {},
            "https://schemas.accounts.firefox.com/event/foobar": {},
            "barfoo": {},
        }

        eq_(0, AccountEvent.objects.count())

        response = self._call_webhook(events, key)

        eq_(202, response.status_code)
        eq_(3, AccountEvent.objects.count())
        eq_(1, process_mock.delay.call_count)

        account_event_1 = AccountEvent.objects.get(event_type=AccountEvent.DELETE_USER)
        account_event_2 = AccountEvent.objects.get(event_type="foobar")
        account_event_3 = AccountEvent.objects.get(event_type="barfoo")

        self.assertEqual(json.loads(account_event_1.body), {})
        self.assertEqual(json.loads(account_event_2.body), {})
        self.assertEqual(json.loads(account_event_3.body), {})
        eq_(account_event_1.status, AccountEvent.UNPROCESSED)
        eq_(account_event_2.status, AccountEvent.NOT_IMPLEMENTED)
        eq_(account_event_3.status, AccountEvent.NOT_IMPLEMENTED)
        eq_(account_event_1.fxa_uid, "54321")
        eq_(account_event_2.fxa_uid, "54321")
        eq_(account_event_3.fxa_uid, "54321")
        eq_(account_event_1.jwt_id, "e19ed6c5-4816-4171-aa43-56ffe80dbda1")
        eq_(account_event_2.jwt_id, "e19ed6c5-4816-4171-aa43-56ffe80dbda1")
        eq_(account_event_3.jwt_id, "e19ed6c5-4816-4171-aa43-56ffe80dbda1")
        eq_(account_event_1.issued_at, "1565720808")
        eq_(account_event_2.issued_at, "1565720808")
        eq_(account_event_3.issued_at, "1565720808")
        eq_(account_event_1.profile, profile)
        eq_(account_event_2.profile, profile)
        eq_(account_event_3.profile, profile)

    @mock.patch("kitsune.users.views.process_event_delete_user")
    @setup_key
    def test_handles_no_user(self, key, process_mock):
        events = {"https://schemas.accounts.firefox.com/event/delete-user": {}}

        eq_(0, AccountEvent.objects.count())

        response = self._call_webhook(events, key)

        eq_(202, response.status_code)
        eq_(1, AccountEvent.objects.count())
        eq_(0, process_mock.delay.call_count)

        account_event = AccountEvent.objects.last()
        eq_(account_event.status, AccountEvent.IGNORED)
        self.assertEqual(json.loads(account_event.body), {})
        eq_(account_event.event_type, AccountEvent.DELETE_USER)
        eq_(account_event.fxa_uid, "54321")
        eq_(account_event.jwt_id, "e19ed6c5-4816-4171-aa43-56ffe80dbda1")
        eq_(account_event.issued_at, "1565720808")
        eq_(account_event.profile, None)

    @setup_key
    def test_invalid_private_key(self, key):
        payload = json.dumps(
            {
                "iss": "http://example.com",
                "sub": "54321",
                "aud": "12345",
                "iat": 1565720808,
                "jti": "e19ed6c5-4816-4171-aa43-56ffe80dbda1",
                "events": {
                    "https://schemas.accounts.firefox.com/event/password-change": {
                        "changeTime": 1565721242227
                    }
                },
            }
        )

        pem = dedent(
            """
        -----BEGIN RSA PRIVATE KEY-----
        MIIBOwIBAAJBAK+qEuIq8XPibyHVbTqk/mPinYKq1CwkPGIs+KjYSUCJdgBIATna
        uETAv/tmlSuyWi+S2RZGqHfrPSnclZ/zFlECAwEAAQJAKmlmm8KAf1kpOcL8107k
        uJsLKnQyO+IXziBLfQCTVwgyoggtyhFgrm+r81/j8bHYAGuPLkOxSoTLgw36ziZH
        wQIhAOHRxpQmT/CQPKt7kvoFa9IOo+mu0CmRsfpQThz3kq2pAiEAxyRIk3cOapT6
        NnVQFPvj2EqNgwYl+uhj6I6wPTbMfGkCIQCrQdJd7KhXgqvgSTlwD8hzZ9L7mC4a
        OHpHobt70G4W8QIhAI1/BGpzP7UPYbHsLRib2crHPkGIzte247ZMHIGCPE1xAiBc
        dDwTPfi5ZdAouUH+T4RCqgS5lrNSB4yah8LxFwFpVg==
        -----END RSA PRIVATE KEY-----
        """
        )
        key = jwk.JWKRSA.load(pem.encode())

        jwt = jws.JWS.sign(
            payload=payload.encode(),
            key=key,
            alg=jwa.RS256,
            kid="123",
            protect=frozenset(["alg", "kid"]),
        ).to_compact()

        eq_(0, AccountEvent.objects.count())

        response = self.client.post(
            reverse("users.fxa_webhook"),
            content_type="",
            HTTP_AUTHORIZATION="Bearer " + jwt.decode(),
        )
        eq_(400, response.status_code)
        eq_(0, AccountEvent.objects.count())

    @setup_key
    def test_id_token(self, key):
        payload = json.dumps(
            {"iss": "http://example.com", "sub": "54321", "aud": "12345", "iat": 1565720808,}
        )

        jwt = jws.JWS.sign(
            payload=payload.encode(),
            key=key,
            alg=jwa.RS256,
            kid="123",
            protect=frozenset(["alg", "kid"]),
        ).to_compact()

        eq_(0, AccountEvent.objects.count())

        response = self.client.post(
            reverse("users.fxa_webhook"),
            content_type="",
            HTTP_AUTHORIZATION="Bearer " + jwt.decode(),
        )
        eq_(400, response.status_code)
        eq_(0, AccountEvent.objects.count())
