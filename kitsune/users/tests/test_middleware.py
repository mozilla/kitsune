from datetime import datetime, timedelta

from django.test.client import RequestFactory
from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib.auth.middleware import AuthenticationMiddleware
from django.contrib.auth.models import AnonymousUser
from django.http import HttpResponseRedirect

from kitsune.users.middleware import LogoutInvalidatedSessionsMiddleware
from kitsune.sumo.tests import TestCase
from kitsune.users.tests import UserFactory, ProfileFactory


class LogoutInvalidatedSessionsMiddlewareTests(TestCase):
    def setUp(self):
        self.request = RequestFactory().request()
        session_middleware = SessionMiddleware()
        session_middleware.process_request(self.request)
        auth_middleware = AuthenticationMiddleware()
        auth_middleware.process_request(self.request)

    def _process_request(self, request):
        middleware = LogoutInvalidatedSessionsMiddleware()
        return middleware.process_request(request)

    def test_does_nothing_to_anonymous_sessions(self):
        session = self.request.session.items()

        self._process_request(self.request)

        self.assertEqual(session, self.request.session.items())

    def test_adds_first_seen_to_users_sessions_once(self):
        self.request.user = UserFactory()

        self._process_request(self.request)
        first_seen = self.request.session["first_seen"]

        assert datetime.utcnow() > first_seen

        self._process_request(self.request)

        self.assertEqual(first_seen, self.request.session["first_seen"])

    def test_does_nothing_if_no_fxa_password_change(self):
        user = UserFactory()
        self.request.user = user
        self.request.session["first_seen"] = datetime.utcfromtimestamp(1)

        self._process_request(self.request)

        self.assertEqual(user, self.request.user)

    def test_logs_out_user_first_seen_before_password_change(self):
        self.request.user = ProfileFactory(
            fxa_password_change=datetime.utcnow() + timedelta(minutes=5)
        ).user

        self._process_request(self.request)
        response = self._process_request(self.request)

        assert isinstance(self.request.user, AnonymousUser)
        assert isinstance(response, HttpResponseRedirect)

    def test_does_nothing_if_user_first_seen_after_password_change(self):
        self.request.user = ProfileFactory(
            fxa_password_change=datetime.utcnow() - timedelta(minutes=5)
        ).user
        user = self.request.user

        self._process_request(self.request)
        self._process_request(self.request)

        self.assertEqual(user, self.request.user)
