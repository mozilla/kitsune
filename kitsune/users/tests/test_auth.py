from unittest.mock import Mock, patch

from django.contrib.auth.models import User
from django.http import HttpRequest
from django.test import RequestFactory, override_settings
from factory.fuzzy import FuzzyChoice

from kitsune.sumo.tests import TestCase
from kitsune.users.auth import FXAAuthBackend
from kitsune.users.models import ContributionAreas
from kitsune.users.tests import GroupFactory, UserFactory


class FXAAuthBackendTests(TestCase):
    @override_settings(FXA_OP_TOKEN_ENDPOINT="https://server.example.com/token")
    @override_settings(FXA_OP_USER_ENDPOINT="https://server.example.com/user")
    @override_settings(FXA_RP_CLIENT_ID="example_id")
    @override_settings(FXA_RP_CLIENT_SECRET="client_secret")
    def setUp(self):
        """Setup class."""
        self.backend = FXAAuthBackend()

    @override_settings(MOZILLA_DOMAINS=["mozilla.org", "mozilla.com", "mozillafoundation.org"])
    def test_is_mozilla_domain_email(self):
        """Test the is_mozilla_domain_email utility function."""
        from kitsune.users.auth import is_mozilla_domain_email

        # Test Mozilla domain emails
        self.assertTrue(is_mozilla_domain_email("user@mozilla.org"))
        self.assertTrue(is_mozilla_domain_email("user@mozilla.com"))
        self.assertTrue(is_mozilla_domain_email("user@mozillafoundation.org"))

        # Test non-Mozilla domain emails
        self.assertFalse(is_mozilla_domain_email("user@example.com"))
        self.assertFalse(is_mozilla_domain_email("user@gmail.com"))

        # Test edge cases
        self.assertFalse(is_mozilla_domain_email(""))
        self.assertFalse(is_mozilla_domain_email(None))
        self.assertFalse(is_mozilla_domain_email("invalid-email"))

    @patch("kitsune.users.auth.messages")
    def test_create_new_profile(self, message_mock):
        """Test that a new profile is created through Mozilla accounts."""
        claims = {
            "email": "bar@example.com",
            "uid": "my_unique_fxa_id",
            "avatar": "http://example.com/avatar",
            "locale": "en-US",
            "displayName": "Crazy Joe Davola",
        }

        request_mock = Mock(spec=HttpRequest)
        request_mock.session = {}
        self.backend.claims = claims
        self.backend.request = request_mock
        users = User.objects.all()
        self.assertEqual(users.count(), 0)
        self.backend.create_user(claims)
        users = User.objects.all()
        self.assertEqual(users.count(), 1)
        self.assertEqual(users[0].email, "bar@example.com")
        self.assertEqual(users[0].username, "bar")
        self.assertEqual(users[0].profile.fxa_uid, "my_unique_fxa_id")
        self.assertEqual(users[0].profile.fxa_avatar, "http://example.com/avatar")
        self.assertEqual(users[0].profile.locale, "en-US")
        self.assertEqual(users[0].profile.name, "Crazy Joe Davola")
        self.assertEqual(0, users[0].groups.count())
        message_mock.success.assert_called()

    @patch("kitsune.users.auth.messages")
    def test_create_new_contributor(self, message_mock):
        """
        Test that a new contributor can be created through Mozilla accounts
        if is_contributor is True in session
        """
        GroupFactory(name=FuzzyChoice(ContributionAreas.get_groups()))
        claims = {
            "email": "crazy_joe_davola@example.com",
            "uid": "abc123",
            "avatar": "http://example.com/avatar",
            "locale": "en-US",
        }

        request_mock = Mock(spec=HttpRequest)
        request_mock.LANGUAGE_CODE = "en"
        request_mock.session = {"contributor": "kb"}
        self.backend.claims = claims
        self.backend.request = request_mock
        users = User.objects.all()
        self.assertEqual(users.count(), 0)
        self.backend.create_user(claims)
        users = User.objects.all()
        self.assertEqual("kb-contributors", users[0].groups.all()[0].name)
        assert "is_contributor" not in request_mock.session
        message_mock.success.assert_called()

    @patch("kitsune.users.auth.messages")
    def test_username_already_exists(self, message_mock):
        """Test account creation when username already exists."""
        UserFactory.create(username="bar")
        claims = {
            "email": "bar@example.com",
            "uid": "my_unique_fxa_id",
        }

        request_mock = Mock(spec=HttpRequest)
        request_mock.session = {}
        self.backend.claims = claims
        self.backend.request = request_mock
        self.backend.create_user(claims)
        user = User.objects.get(profile__fxa_uid="my_unique_fxa_id")
        self.assertEqual(user.username, "bar1")
        message_mock.success.assert_called()

    def test_login_existing_user_by_fxa_uid(self):
        """Test user filtering by FxA uid."""
        user = UserFactory.create(profile__fxa_uid="my_unique_fxa_id")
        claims = {
            "uid": "my_unique_fxa_id",
        }

        request_mock = Mock(spec=HttpRequest)
        request_mock.session = {}
        self.backend.claims = claims
        self.backend.request = request_mock
        self.backend.request.user = user
        self.backend.filter_users_by_claims(claims)
        self.assertEqual(User.objects.all()[0].id, user.id)

    @patch("kitsune.users.auth.messages")
    def test_connecting_using_existing_fxa_account(self, message_mock):
        """Test connecting a SUMO account with an existing FxA in SUMO."""
        UserFactory.create(profile__fxa_uid="my_unique_fxa_id")
        user = UserFactory.create()
        claims = {
            "uid": "my_unique_fxa_id",
        }
        # Test without a request (for example, when called from a Celery task).
        with self.subTest("without a request"):
            self.backend.update_user(user, claims)
            assert not message_mock.error.called
        # Test with a request.
        request_mock = Mock(spec=HttpRequest)
        request_mock.session = {}
        with self.subTest("with a request"):
            self.backend.request = request_mock
            self.backend.update_user(user, claims)
            message_mock.error.assert_called_with(
                request_mock, "This Mozilla account is already used in another profile."
            )

    def test_login_existing_user_by_email(self):
        """Test user filtering by email."""
        user = UserFactory.create(email="bar@example.com")
        claims = {
            "email": "bar@example.com",
        }

        request_mock = Mock(spec=HttpRequest)
        self.backend.claims = claims
        self.backend.request = request_mock
        self.backend.request.user = user
        self.backend.filter_users_by_claims(claims)
        self.assertEqual(User.objects.all()[0].id, user.id)

    @patch("kitsune.users.auth.messages")
    def test_email_changed_in_FxA_match_by_uid(self, message_mock):
        """Test that the user email is updated successfully if it
        is changed in Mozilla accounts and we match users by uid.
        """
        user = UserFactory.create(
            profile__fxa_uid="my_unique_fxa_id",
            email="foo@example.com",
        )
        claims = {"uid": "my_unique_fxa_id", "email": "bar@example.com", "subscriptions": "[]"}
        self.backend.update_user(user, claims)
        user = User.objects.get(id=user.id)
        self.assertEqual(user.email, "bar@example.com")
        assert not message_mock.info.called

    @patch("kitsune.users.auth.messages")
    @patch("mozilla_django_oidc.auth.requests")
    @patch("mozilla_django_oidc.auth.OIDCAuthenticationBackend.verify_token")
    def test_link_sumo_account_fxa(self, verify_token_mock, requests_mock, message_mock):
        """Test that an existing SUMO account is succesfully linked to Mozilla account."""
        verify_token_mock.return_value = True

        user = UserFactory.create(email="sumo@example.com", profile__name="Kenny Bania")
        auth_request = RequestFactory().get("/foo", {"code": "foo", "state": "bar"})
        auth_request.session = {}
        auth_request.user = user

        get_json_mock = Mock()
        get_json_mock.json.return_value = {
            "email": "fxa@example.com",
            "uid": "my_unique_fxa_id",
            "avatar": "http://example.com/avatar",
            "locale": "en-US",
            "displayName": "FXA Display name",
            "subscriptions": "[]",
        }
        requests_mock.get.return_value = get_json_mock

        post_json_mock = Mock()
        post_json_mock.status_code = 200
        post_json_mock.json.return_value = {
            "id_token": "id_token",
            "access_token": "access_granted",
        }
        requests_mock.post.return_value = post_json_mock

        self.backend.authenticate(auth_request)
        self.assertEqual(user.email, "fxa@example.com")
        self.assertEqual(user.profile.name, "Kenny Bania")
        message_mock.info.assert_called_with(auth_request, "fxa_notification_updated")

    @patch("kitsune.users.auth.messages")
    def test_update_email_already_exists(self, message_mock):
        """Test updating to an email that is already used."""
        UserFactory.create(email="foo@example.com")
        user = UserFactory.create(email="bar@example.com")
        claims = {"uid": "my_unique_fxa_id", "email": "foo@example.com"}
        # Test without a request (for example, when called from a Celery task).
        with self.subTest("without a request"):
            self.backend.update_user(user, claims)
            assert not message_mock.error.called
            self.assertEqual(User.objects.get(id=user.id).email, "bar@example.com")
        # Test with a request.
        request_mock = Mock(spec=HttpRequest)
        request_mock.session = {}
        with self.subTest("with a request"):
            self.backend.request = request_mock
            self.backend.update_user(user, claims)
            message_mock.error.assert_called_with(
                request_mock,
                "The e-mail address used with this Mozilla account"
                " is already linked in another profile.",
            )
            self.assertEqual(User.objects.get(id=user.id).email, "bar@example.com")

    @patch("kitsune.users.auth.messages")
    @override_settings(MOZILLA_DOMAINS=["mozilla.org", "mozilla.com"])
    def test_create_user_with_mozilla_domain_email(self, message_mock):
        """Test that is_mozilla_staff is set to True for Mozilla domain emails."""
        claims = {
            "email": "user@mozilla.org",
            "uid": "my_unique_fxa_id",
            "avatar": "http://example.com/avatar",
            "locale": "en-US",
            "displayName": "Mozilla User",
        }

        request_mock = Mock(spec=HttpRequest)
        request_mock.session = {}
        self.backend.claims = claims
        self.backend.request = request_mock
        users = User.objects.all()
        self.assertEqual(users.count(), 0)
        self.backend.create_user(claims)
        users = User.objects.all()
        self.assertEqual(users.count(), 1)
        self.assertTrue(users[0].profile.is_mozilla_staff)
        message_mock.success.assert_called()

    @patch("kitsune.users.auth.messages")
    @override_settings(MOZILLA_DOMAINS=["mozilla.org", "mozilla.com"])
    def test_create_user_with_non_mozilla_domain_email(self, message_mock):
        """Test that is_mozilla_staff is set to False for non-Mozilla domain emails."""
        claims = {
            "email": "user@example.com",
            "uid": "my_unique_fxa_id",
            "avatar": "http://example.com/avatar",
            "locale": "en-US",
            "displayName": "Regular User",
        }

        request_mock = Mock(spec=HttpRequest)
        request_mock.session = {}
        self.backend.claims = claims
        self.backend.request = request_mock
        users = User.objects.all()
        self.assertEqual(users.count(), 0)
        self.backend.create_user(claims)
        users = User.objects.all()
        self.assertEqual(users.count(), 1)
        self.assertFalse(users[0].profile.is_mozilla_staff)
        message_mock.success.assert_called()

    @patch("kitsune.users.auth.messages")
    @override_settings(MOZILLA_DOMAINS=["mozilla.org", "mozilla.com"])
    def test_update_user_email_to_mozilla_domain(self, message_mock):
        """Test that is_mozilla_staff is updated when email changes to Mozilla domain."""
        user = UserFactory.create(
            profile__fxa_uid="my_unique_fxa_id",
            email="user@example.com",
            profile__is_fxa_migrated=True,
            profile__is_mozilla_staff=False,
        )
        claims = {"uid": "my_unique_fxa_id", "email": "user@mozilla.org", "subscriptions": "[]"}
        self.backend.update_user(user, claims)
        user = User.objects.get(id=user.id)
        self.assertEqual(user.email, "user@mozilla.org")
        self.assertTrue(user.profile.is_mozilla_staff)
        assert not message_mock.info.called

    @patch("kitsune.users.auth.messages")
    @override_settings(MOZILLA_DOMAINS=["mozilla.org", "mozilla.com"])
    def test_update_user_email_from_mozilla_domain(self, message_mock):
        """Test that is_mozilla_staff is updated when email changes from Mozilla domain."""
        user = UserFactory.create(
            profile__fxa_uid="my_unique_fxa_id",
            email="user@mozilla.org",
            profile__is_fxa_migrated=True,
            profile__is_mozilla_staff=True,
        )
        claims = {"uid": "my_unique_fxa_id", "email": "user@example.com", "subscriptions": "[]"}
        self.backend.update_user(user, claims)
        user = User.objects.get(id=user.id)
        self.assertEqual(user.email, "user@example.com")
        self.assertFalse(user.profile.is_mozilla_staff)
        assert not message_mock.info.called

    @patch("kitsune.users.auth.messages")
    @override_settings(MOZILLA_DOMAINS=["mozilla.org", "mozilla.com"])
    def test_fxa_migration_sets_mozilla_staff_flag(self, message_mock):
        """Test that is_mozilla_staff is set during FxA migration."""
        user = UserFactory.create(
            email="user@mozilla.org",
            profile__is_fxa_migrated=False,
            profile__is_mozilla_staff=False,
        )
        claims = {"uid": "my_unique_fxa_id", "email": "user@mozilla.org", "subscriptions": "[]"}

        request_mock = Mock(spec=HttpRequest)
        request_mock.session = {}
        self.backend.request = request_mock

        self.backend.update_user(user, claims)
        user = User.objects.get(id=user.id)
        self.assertTrue(user.profile.is_fxa_migrated)
        self.assertTrue(user.profile.is_mozilla_staff)
        message_mock.info.assert_called_with(request_mock, "fxa_notification_updated")
