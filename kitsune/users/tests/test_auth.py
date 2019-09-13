from django.contrib.auth.models import User
from django.http import HttpRequest
from django.test import RequestFactory, override_settings

from mock import Mock, patch
from nose.tools import eq_, ok_

from kitsune.sumo.tests import TestCase
from kitsune.users.auth import FXAAuthBackend
from kitsune.users.tests import UserFactory, GroupFactory
from kitsune.users.models import CONTRIBUTOR_GROUP


class FXAAuthBackendTests(TestCase):

    @override_settings(FXA_OP_TOKEN_ENDPOINT='https://server.example.com/token')
    @override_settings(FXA_OP_USER_ENDPOINT='https://server.example.com/user')
    @override_settings(FXA_RP_CLIENT_ID='example_id')
    @override_settings(FXA_RP_CLIENT_SECRET='client_secret')
    def setUp(self):
        """Setup class."""
        self.backend = FXAAuthBackend()

    @patch('kitsune.users.auth.messages')
    def test_create_new_profile(self, message_mock):
        """Test that a new profile is created through Firefox Accounts."""
        claims = {
            'email': 'bar@example.com',
            'uid': 'my_unique_fxa_id',
            'avatar': 'http://example.com/avatar',
            'locale': 'en-US',
            'displayName': 'Crazy Joe Davola',
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
        eq_(users[0].profile.fxa_avatar, 'http://example.com/avatar')
        eq_(users[0].profile.locale, 'en-US')
        eq_(users[0].profile.name, 'Crazy Joe Davola')
        eq_(0, users[0].groups.count())
        message_mock.info.assert_called_with(request_mock, 'fxa_notification_created')

    @patch('kitsune.users.auth.messages')
    def test_create_new_contributor(self, message_mock):
        """
        Test that a new contributor can be created through Firefox Accounts
        if is_contributor is True in session
        """
        GroupFactory(name=CONTRIBUTOR_GROUP)
        claims = {
            'email': 'crazy_joe_davola@example.com',
            'uid': 'abc123',
            'avatar': 'http://example.com/avatar',
            'locale': 'en-US'
        }

        request_mock = Mock(spec=HttpRequest)
        request_mock.LANGUAGE_CODE = 'en'
        request_mock.session = {
            'is_contributor': True
        }
        self.backend.claims = claims
        self.backend.request = request_mock
        users = User.objects.all()
        eq_(users.count(), 0)
        self.backend.create_user(claims)
        users = User.objects.all()
        eq_(CONTRIBUTOR_GROUP, users[0].groups.all()[0].name)
        ok_('is_contributor' not in request_mock.session)
        message_mock.info.assert_called_with(
            request_mock,
            'fxa_notification_created'
        )

    @patch('kitsune.users.auth.messages')
    def test_username_already_exists(self, message_mock):
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
        message_mock.info.assert_called_with(
            request_mock,
            'fxa_notification_created'
        )

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

    @patch('kitsune.users.auth.messages')
    def test_connecting_using_existing_fxa_account(self, message_mock):
        """Test connecting a SUMO account with an existing FxA in SUMO."""
        UserFactory.create(profile__fxa_uid='my_unique_fxa_id')
        user = UserFactory.create()
        claims = {
            'uid': 'my_unique_fxa_id',
        }
        request_mock = Mock(spec=HttpRequest)
        request_mock.session = {}
        self.backend.claims = claims
        self.backend.request = request_mock
        self.backend.update_user(user, claims)
        message_mock.error.assert_called_with(
            request_mock,
            u'This Firefox Account is already used in another profile.'
        )
        ok_(not User.objects.get(id=user.id).profile.is_fxa_migrated)
        ok_(not User.objects.get(id=user.id).profile.fxa_uid)

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

    @patch('kitsune.users.auth.messages')
    def test_email_changed_in_FxA_match_by_uid(self, message_mock):
        """Test that the user email is updated successfully if it
        is changed in Firefox Accounts and we match users by uid.
        """
        user = UserFactory.create(profile__fxa_uid='my_unique_fxa_id',
                                  email='foo@example.com',
                                  profile__is_fxa_migrated=True)
        claims = {
            'uid': 'my_unique_fxa_id',
            'email': 'bar@example.com',
            'subscriptions': '[]'
        }
        request_mock = Mock(spec=HttpRequest)
        request_mock.session = {}
        self.backend.claims = claims
        self.backend.request = request_mock
        self.backend.update_user(user, claims)
        user = User.objects.get(id=user.id)
        eq_(user.email, 'bar@example.com')
        ok_(not message_mock.info.called)

    @patch('kitsune.users.auth.messages')
    @patch('mozilla_django_oidc.auth.requests')
    @patch('mozilla_django_oidc.auth.OIDCAuthenticationBackend.verify_token')
    def test_link_sumo_account_fxa(self, verify_token_mock, requests_mock, message_mock):
        """Test that an existing SUMO account is succesfully linked to Firefox Account."""

        verify_token_mock.return_value = True

        user = UserFactory.create(email='sumo@example.com',
                                  profile__avatar='sumo_avatar',
                                  profile__name='Kenny Bania')
        auth_request = RequestFactory().get('/foo', {'code': 'foo',
                                                     'state': 'bar'})
        auth_request.session = {}
        auth_request.user = user

        get_json_mock = Mock()
        get_json_mock.json.return_value = {
            'email': 'fxa@example.com',
            'uid': 'my_unique_fxa_id',
            'avatar': 'http://example.com/avatar',
            'locale': 'en-US',
            'displayName': 'FXA Display name',
            'subscriptions': '[]'
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
        eq_(user.profile.name, 'Kenny Bania')
        message_mock.info.assert_called_with(
            auth_request,
            'fxa_notification_updated'
        )

    @patch('kitsune.users.auth.messages')
    def test_update_email_already_exists(self, message_mock):
        """Test updating to an email that is already used."""
        UserFactory.create(email='foo@example.com')
        user = UserFactory.create(email='bar@example.com')
        claims = {
            'uid': 'my_unique_fxa_id',
            'email': 'foo@example.com'
        }
        request_mock = Mock(spec=HttpRequest)
        request_mock.session = {}
        self.backend.claims = claims
        self.backend.request = request_mock
        self.backend.update_user(user, claims)
        message_mock.error.assert_called_with(
            request_mock,
            u'The email used with this Firefox Account is already linked in another profile.'
        )
        eq_(User.objects.get(id=user.id).email, 'bar@example.com')
