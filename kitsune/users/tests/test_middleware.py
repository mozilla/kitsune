from datetime import UTC, datetime, timedelta

from django.contrib.auth.models import AnonymousUser
from django.contrib.sessions.middleware import SessionMiddleware
from django.http import HttpResponse, HttpResponseRedirect
from django.test.client import RequestFactory
from django.utils.timezone import now as timezone_now

from kitsune.sumo.tests import TestCase
from kitsune.users.middleware import LogoutInvalidatedSessionsMiddleware
from kitsune.users.tests import ProfileFactory, UserFactory


class LogoutInvalidatedSessionsMiddlewareTests(TestCase):
    def setUp(self):
        self.get_response = lambda *args, **kwargs: HttpResponse()
        self.request = self._new_request()

    def _new_request(self):
        request = RequestFactory().request()
        SessionMiddleware(self.get_response).process_request(request)
        return request

    def _process_request(self, request):
        middleware = LogoutInvalidatedSessionsMiddleware(self.get_response)
        return middleware.process_request(request)

    def test_does_nothing_to_anonymous_sessions(self):
        self.request.user = AnonymousUser()
        session = self.request.session.items()
        self._process_request(self.request)
        self.assertEqual(session, self.request.session.items())

    def test_adds_first_seen_to_users_sessions_once(self):
        self.request.user = UserFactory()

        self._process_request(self.request)

        first_seen = self.request.session["first_seen"]
        first_seen_dt = datetime.fromisoformat(first_seen)
        self.assertGreater(timezone_now(), first_seen_dt)

        self._process_request(self.request)

        self.assertEqual(first_seen, self.request.session["first_seen"])

    def test_logs_out_sessions_first_seen_before_the_password_change(self):
        now = timezone_now()
        # Old sessions stored naive datetime objects via datetime.utcnow().
        legacy_now = datetime.now(UTC).replace(tzinfo=None)
        for name, password_change, first_seen, logged_out in (
            ("no password change", None, now.isoformat(), False),
            ("changed after first seen", now + timedelta(minutes=5), now.isoformat(), True),
            ("changed before first seen", now - timedelta(minutes=5), now.isoformat(), False),
            ("legacy, changed after", now + timedelta(minutes=5), legacy_now, True),
            ("legacy, changed before", now - timedelta(minutes=5), legacy_now, False),
        ):
            with self.subTest(name):
                request = self._new_request()
                request.user = user = ProfileFactory(fxa_password_change=password_change).user
                request.session["first_seen"] = first_seen

                response = self._process_request(request)

                if logged_out:
                    self.assertIsInstance(request.user, AnonymousUser)
                    self.assertIsInstance(response, HttpResponseRedirect)
                else:
                    self.assertEqual(user, request.user)
                    self.assertIsNone(response)
