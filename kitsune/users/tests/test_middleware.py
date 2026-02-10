from datetime import UTC, datetime, timedelta

from django.contrib.auth.middleware import AuthenticationMiddleware
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
        self.request = RequestFactory().request()
        self.get_response = lambda *args, **kwargs: HttpResponse()
        session_middleware = SessionMiddleware(self.get_response)
        session_middleware.process_request(self.request)
        auth_middleware = AuthenticationMiddleware(self.get_response)
        auth_middleware.process_request(self.request)

    def _process_request(self, request):
        middleware = LogoutInvalidatedSessionsMiddleware(self.get_response)
        return middleware.process_request(request)

    def test_does_nothing_to_anonymous_sessions(self):
        session = self.request.session.items()

        self._process_request(self.request)

        self.assertEqual(session, self.request.session.items())

    def test_adds_first_seen_to_users_sessions_once(self):
        self.request.user = UserFactory()

        self._process_request(self.request)
        first_seen = self.request.session["first_seen"]

        first_seen_dt = datetime.fromisoformat(first_seen)
        assert timezone_now() > first_seen_dt

        self._process_request(self.request)

        self.assertEqual(first_seen, self.request.session["first_seen"])

    def test_does_nothing_if_no_fxa_password_change(self):
        user = UserFactory()
        self.request.user = user
        self.request.session["first_seen"] = datetime.fromtimestamp(1, UTC).isoformat()

        self._process_request(self.request)

        self.assertEqual(user, self.request.user)

    def test_logs_out_user_first_seen_before_password_change(self):
        self.request.user = ProfileFactory(
            fxa_password_change=timezone_now() + timedelta(minutes=5)
        ).user

        self._process_request(self.request)
        response = self._process_request(self.request)

        assert isinstance(self.request.user, AnonymousUser)
        assert isinstance(response, HttpResponseRedirect)

    def test_does_nothing_if_user_first_seen_after_password_change(self):
        self.request.user = ProfileFactory(
            fxa_password_change=timezone_now() - timedelta(minutes=5)
        ).user
        user = self.request.user

        self._process_request(self.request)
        self._process_request(self.request)

        self.assertEqual(user, self.request.user)
