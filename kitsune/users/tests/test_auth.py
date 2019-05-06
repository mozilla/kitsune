from django.contrib.auth.models import User
from django.http import HttpRequest
from django.test import RequestFactory, override_settings

from mock import Mock, patch
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
        request_mock.session = {}
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
        request_mock.session = {}
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
        request_mock.session = {}
        self.backend.claims = claims
        self.backend.request = request_mock
        self.backend.request.user = user
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
        self.backend.request.user = user
        self.backend.filter_users_by_claims(claims)
        eq_(User.objects.all()[0].id, user.id)

    def test_email_changed_in_FxA_match_by_uid(self):
        """Test that the user email is updated successfully if it
        is changed in Firefox Accounts and we match users by uid.
        """
        user = UserFactory.create(profile__fxa_uid='my_unique_fxa_id',
                                  email='foo@example.com')
        claims = {
            'uid': 'my_unique_fxa_id',
            'email': 'bar@example.com'
        }
        request_mock = Mock(spec=HttpRequest)
        request_mock.session = {}
        self.backend.claims = claims
        self.backend.request = request_mock
        self.backend.update_user(user, claims)
        user = User.objects.get(id=user.id)
        eq_(user.email, 'bar@example.com')

    @patch('mozilla_django_oidc.auth.requests')
    @patch('mozilla_django_oidc.auth.OIDCAuthenticationBackend.verify_token')
    def test_link_sumo_account_fxa(self, verify_token_mock, requests_mock):
        """Test that an existing SUMO account is succesfully linke to Firefox Account."""

        verify_token_mock.return_value = True

        user = UserFactory.create(email='sumo@example.com',
                                  profile__avatar='sumo_avatar')
        ok_(not user.profile.is_fxa_migrated)
        auth_request = RequestFactory().get('/foo', {'code': 'foo',
                                                     'state': 'bar'})
        auth_request.session = {}
        auth_request.user = user

        get_json_mock = Mock()
        get_json_mock.json.return_value = {
            'email': 'fxa@example.com',
            'uid': 'my_unique_fxa_id',
            'avatar': 'http://example.com/avatar',
            'locale': 'en-US'
        }
        requests_mock.get.return_value = get_json_mock

        post_json_mock = Mock()
        post_json_mock.json.return_value = {
            'id_token': 'id_token',
            'access_token': 'access_granted'
        }
        requests_mock.post.return_value = post_json_mock

        self.backend.authenticate(auth_request)
        ok_(user.profile.is_fxa_migrated)
        eq_(user.profile.fxa_uid, 'my_unique_fxa_id')
        eq_(user.email, 'fxa@example.com')
        eq_(user.profile.avatar, 'sumo_avatar')
