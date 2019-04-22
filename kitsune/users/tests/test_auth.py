from django.contrib.auth.models import User
from django.http import HttpRequest
from django.test import override_settings

from mock import Mock
from nose.tools import eq_, ok_

from kitsune.sumo.tests import TestCase
from kitsune.users.auth import FXAAuthBackend
from kitsune.users.tests import UserFactory


class FXAAuthBackendTests(TestCase):

    @override_settings(FXA_OP_TOKEN_ENDPOINT='https://server.example.com/token')
    @override_settings(FXA_OP_USER_ENDPOINT='https://server.example.com/user')
    @override_settings(FXA_RP_CLIENT_ID='example_id')
    @override_settings(FXA_RP_CLIENT_SECRET='client_secret')
    def setUp(self):
        """Setup class."""
        self.backend = FXAAuthBackend()

    def test_create_new_profile(self):
        """Test that a new profile is created through Firefox Accounts."""
        claims = {
            'email': 'bar@example.com',
            'uid': 'my_unique_fxa_id',
            'avatar': 'http://example.com/avatar',
            'locale': 'en-US'
        }

        request_mock = Mock(spec=HttpRequest)
        self.backend.claims = claims
        self.backend.request = request_mock
        users = User.objects.all()
        eq_(users.count(), 0)
        self.backend.create_user(claims)
        users = User.objects.all()
        eq_(users.count(), 1)
        eq_(users[0].email, 'bar@example.com')
        eq_(users[0].username, 'bar')
        eq_(users[0].profile.fxa_uid, 'my_unique_fxa_id')
        eq_(users[0].profile.avatar, 'http://example.com/avatar')
        eq_(users[0].profile.locale, 'en-US')

    def test_username_already_exists(self):
        """Test account creation when username already exists."""
        UserFactory.create(username='bar')
        claims = {
            'email': 'bar@example.com',
            'uid': 'my_unique_fxa_id',
        }

        request_mock = Mock(spec=HttpRequest)
        self.backend.claims = claims
        self.backend.request = request_mock
        self.backend.create_user(claims)
        user = User.objects.get(profile__fxa_uid='my_unique_fxa_id')
        eq_(user.username, 'bar1')

    def test_login_fxa_uid_missing(self):
        """Test user filtering without FxA uid."""
        claims = {
            'uid': '',
        }

        request_mock = Mock(spec=HttpRequest)
        self.backend.claims = claims
        self.backend.request = request_mock
        ok_(not self.backend.filter_users_by_claims(claims))

    def test_login_existing_user_by_fxa_uid(self):
        """Test user filtering by FxA uid."""
        user = UserFactory.create(profile__fxa_uid='my_unique_fxa_id')
        claims = {
            'uid': 'my_unique_fxa_id',
        }

        request_mock = Mock(spec=HttpRequest)
        self.backend.claims = claims
        self.backend.request = request_mock
        self.backend.filter_users_by_claims(claims)
        eq_(User.objects.all()[0].id, user.id)

    def test_login_existing_user_by_email(self):
        """Test user filtering by email."""
        user = UserFactory.create(email='bar@example.com')
        claims = {
            'email': 'bar@example.com',
        }

        request_mock = Mock(spec=HttpRequest)
        self.backend.claims = claims
        self.backend.request = request_mock
        self.backend.filter_users_by_claims(claims)
        eq_(User.objects.all()[0].id, user.id)
