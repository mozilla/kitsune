from unittest.mock import Mock, patch

from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import SuspiciousOperation
from django.db import transaction
from django.http import HttpRequest
from django.test import RequestFactory, override_settings
from factory.fuzzy import FuzzyChoice

from kitsune.groups.models import EnterpriseInvitation, GroupProfile
from kitsune.groups.tests import GroupProfileFactory
from kitsune.products.tests import ProductFactory
from kitsune.sumo.tests import TestCase
from kitsune.users.auth import FXAAuthBackend, is_mozilla_domain_email
from kitsune.users.models import ContributionAreas, Profile
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
        self.assertEqual("kb-contributors", users[0].groups.all()[0].name)  # noqa: group-leak
        assert "is_contributor" not in request_mock.session
        message_mock.success.assert_called()

    @patch("kitsune.users.auth.messages")
    def test_username_already_exists(self, message_mock):
        """Test account creation when username already exists."""
        UserFactory.create(username="bar", email="bar@other.example.com")
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

    def test_login_fxa_uid_missing(self):
        """Test user filtering without FxA uid."""
        claims = {
            "uid": "",
        }

        request_mock = Mock(spec=HttpRequest)
        self.backend.claims = claims
        self.backend.request = request_mock
        assert not self.backend.filter_users_by_claims(claims)

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
        """update_user must not link an existing account to the FxA uid in the claims."""
        UserFactory.create(profile__fxa_uid="my_unique_fxa_id")
        user = UserFactory.create()
        user.profile.is_fxa_migrated = False
        user.profile.save()
        claims = {
            "uid": "my_unique_fxa_id",
        }
        # Test without a request (for example, when called from a Celery task).
        with self.subTest("without a request"):
            self.backend.update_user(user, claims)
            assert not message_mock.error.called
            assert not User.objects.get(id=user.id).profile.is_fxa_migrated
            assert not User.objects.get(id=user.id).profile.fxa_uid
        # Test with a request.
        request_mock = Mock(spec=HttpRequest)
        request_mock.session = {}
        with self.subTest("with a request"):
            self.backend.request = request_mock
            self.backend.update_user(user, claims)
            assert not message_mock.error.called
            assert not User.objects.get(id=user.id).profile.is_fxa_migrated
            assert not User.objects.get(id=user.id).profile.fxa_uid

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
            profile__is_fxa_migrated=True,
        )
        claims = {"uid": "my_unique_fxa_id", "email": "bar@example.com", "subscriptions": "[]"}
        self.backend.update_user(user, claims)
        user = User.objects.get(id=user.id)
        self.assertEqual(user.email, "bar@example.com")
        assert not message_mock.info.called

    @patch("kitsune.users.auth.messages")
    @patch("mozilla_django_oidc.auth.requests")
    @patch("mozilla_django_oidc.auth.OIDCAuthenticationBackend.verify_token")
    def test_existing_sumo_account_not_linked_to_fxa(
        self, verify_token_mock, requests_mock, message_mock
    ):
        """An authenticated existing SUMO account must not be auto-linked to FxA on login."""

        verify_token_mock.return_value = True

        user = UserFactory.create(email="sumo@example.com", profile__name="Kenny Bania")
        user.profile.is_fxa_migrated = False
        user.profile.save()
        auth_request = RequestFactory().get("/foo", {"code": "foo", "state": "bar"})
        auth_request.session = {}
        auth_request.user = user

        get_json_mock = Mock()
        get_json_mock.json.return_value = {
            "email": "sumo@example.com",
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
        user = User.objects.get(id=user.id)
        assert not user.profile.is_fxa_migrated
        assert not user.profile.fxa_uid
        self.assertEqual(user.email, "sumo@example.com")
        self.assertEqual(User.objects.count(), 1)
        assert not message_mock.info.called

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
            message_mock.error.assert_called_once()
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
    def test_update_user_sets_mozilla_staff_flag(self, message_mock):
        """Test that is_mozilla_staff is set when updating a Mozilla domain user."""
        user = UserFactory.create(
            email="user@mozilla.org",
            profile__is_mozilla_staff=False,
        )
        claims = {"uid": "my_unique_fxa_id", "email": "user@mozilla.org", "subscriptions": "[]"}

        request_mock = Mock(spec=HttpRequest)
        request_mock.session = {}
        self.backend.request = request_mock

        self.backend.update_user(user, claims)
        user = User.objects.get(id=user.id)
        self.assertTrue(user.profile.is_mozilla_staff)
        assert not message_mock.info.called

    @override_settings(FXA_RP_SCOPES="openid email")
    def test_dispatch_verifies_claims_before_mutating_accounts(self):
        user = UserFactory(profile__fxa_uid="existing-uid", profile__name="Original")
        with (
            patch.object(
                self.backend,
                "get_userinfo",
                return_value={"uid": "existing-uid", "displayName": "Unverified"},
            ),
            self.assertRaises(SuspiciousOperation),
        ):
            self.backend.get_or_create_user("access", "id", {})
        user.profile.refresh_from_db()
        self.assertEqual(user.profile.name, "Original")
        self.assertEqual(User.all_users.count(), 1)

    @patch("kitsune.users.auth.messages")
    def test_dispatch_creates_then_reuses_one_account(self, messages_mock):
        self.backend.request = RequestFactory().get("/")
        self.backend.request.session = {}
        claims = {"email": "ordinary@example.com", "uid": "ordinary-uid"}
        with patch.object(self.backend, "get_userinfo", return_value=claims):
            created = self.backend.get_or_create_user("access", "id", {})
            reused = self.backend.get_or_create_user("access", "id", {})
        self.assertEqual(reused.pk, created.pk)
        self.assertEqual(User.all_users.filter(email=claims["email"]).count(), 1)
        self.assertEqual(reused.profile.fxa_uid, "ordinary-uid")
        self.assertTrue(reused.profile.is_fxa_migrated)

    @override_settings(FXA_CREATE_USER=False)
    def test_dispatch_honors_disabled_account_creation(self):
        claims = {"email": "unregistered@example.com", "uid": "unregistered-uid"}
        with patch.object(self.backend, "get_userinfo", return_value=claims):
            self.assertIsNone(self.backend.get_or_create_user("access", "id", {}))
        self.assertFalse(User.all_users.filter(email=claims["email"]).exists())

    def test_email_fallback_preserves_legacy_no_auto_link_without_uid(self):
        user = UserFactory(
            email="legacy@example.com",
            profile__fxa_uid=None,
            profile__is_fxa_migrated=False,
            profile__name="Existing name",
        )
        with patch.object(
            self.backend, "get_userinfo", return_value={"email": "legacy@example.com"}
        ):
            reused = self.backend.get_or_create_user("access", "id", {})
        self.assertEqual(reused.pk, user.pk)
        user.profile.refresh_from_db()
        self.assertIsNone(user.profile.fxa_uid)
        self.assertFalse(user.profile.is_fxa_migrated)
        self.assertEqual(user.profile.name, "Existing name")
        self.assertEqual(User.all_users.count(), 1)

    def test_hidden_and_duplicate_email_matches_cannot_create_or_mutate_accounts(self):
        for account_types in (
            (Profile.AccountType.SYSTEM,),
            (Profile.AccountType.REGULAR, Profile.AccountType.SYSTEM),
        ):
            with self.subTest(account_types=account_types):
                email = f"blocked-{len(account_types)}@example.com"
                for index, account_type in enumerate(account_types):
                    UserFactory(
                        email=email.upper() if index == 0 else email,
                        profile__account_type=account_type,
                        profile__name="Original",
                    )
                users_before = list(User.all_users.order_by("pk").values())
                profiles_before = list(Profile.all_profiles.order_by("pk").values())
                claims = {"email": email, "uid": "new-uid", "displayName": "Replacement"}
                for recheck in (False, True):
                    with self.subTest(creation_recheck=recheck):
                        with (
                            patch.object(self.backend, "get_userinfo", return_value=claims),
                            self.assertRaises(SuspiciousOperation),
                        ):
                            if recheck:
                                self.backend.create_user(claims)
                            else:
                                self.backend.get_or_create_user("access", "id", {})
                        self.assertEqual(
                            list(User.all_users.order_by("pk").values()), users_before
                        )
                        self.assertEqual(
                            list(Profile.all_profiles.order_by("pk").values()), profiles_before
                        )

    def _create_prepared_user(self):
        user = UserFactory(
            email="invited@example.com",
            password=None,
            is_active=False,
            profile__fxa_uid=None,
            profile__is_fxa_migrated=False,
            profile__name="",
        )
        company = GroupProfile.objects.add_child(
            GroupProfileFactory(), create_kwargs={"group": GroupFactory()}
        )
        EnterpriseInvitation.objects.create(
            company=company,
            email=user.email,
            user=user,
            created_user=True,
            completed_actions=["sumo_account"],
        )
        return user

    def test_prepared_user_cannot_bypass_invitation_through_ordinary_login(self):
        user = self._create_prepared_user()
        for uid in ("authenticated-uid", None):
            with self.subTest(uid=uid):
                claims = {
                    "email": "INVITED@example.com",
                    "displayName": "Should not be saved",
                    "avatar": "https://example.com/avatar.png",
                }
                if uid:
                    claims["uid"] = uid
                with (
                    patch.object(self.backend, "get_userinfo", return_value=claims),
                    self.assertRaises(SuspiciousOperation),
                ):
                    self.backend.get_or_create_user("access", "id", {})
                user.refresh_from_db()
                self.assertFalse(user.is_active)
                self.assertFalse(user.has_usable_password())
                self.assertIsNone(user.profile.fxa_uid)
                self.assertFalse(user.profile.is_fxa_migrated)
                self.assertEqual(user.profile.name, "")
                self.assertEqual(user.profile.fxa_avatar, "")
                self.assertEqual(User.all_users.count(), 1)

    def test_background_update_cannot_modify_a_prepared_user(self):
        user = self._create_prepared_user()
        with self.assertRaises(SuspiciousOperation):
            self.backend.update_user(
                user, {"email": "changed@example.com", "displayName": "Should not be saved"}
            )
        user.refresh_from_db()
        self.assertEqual(user.email, "invited@example.com")
        self.assertEqual(user.profile.name, "")
        self.assertIsNone(user.profile.fxa_uid)

    def test_email_update_refuses_case_insensitive_hidden_collision_before_mutation(self):
        UserFactory(email="TAKEN@example.com", profile__account_type=Profile.AccountType.SYSTEM)
        user = UserFactory(
            email="original@example.com",
            profile__name="",
            profile__fxa_avatar="https://example.com/original.png",
        )
        product = ProductFactory()
        user.profile.products.add(product)
        claims = {
            "email": "taken@example.com",
            "displayName": "Should not be saved",
            "avatar": "https://example.com/replacement.png",
            "subscriptions": [],
        }
        self.assertIsNone(self.backend.update_user(user, claims))
        user.refresh_from_db()
        self.assertEqual(user.email, "original@example.com")
        self.assertEqual(user.profile.name, "")
        self.assertEqual(user.profile.fxa_avatar, "https://example.com/original.png")
        self.assertEqual(list(user.profile.products.values_list("pk", flat=True)), [product.pk])

    def test_staff_group_retains_email_even_when_claimed_address_is_taken(self):
        UserFactory(email="claimed@example.com")
        user = UserFactory(
            email="local@example.com",
            profile__name="",
            groups=[GroupFactory(name=settings.STAFF_GROUP)],
        )
        result = self.backend.update_user(
            user, {"email": "claimed@example.com", "displayName": "Provider name"}
        )
        self.assertEqual(result.pk, user.pk)
        user.refresh_from_db()
        self.assertEqual(user.email, "local@example.com")
        self.assertEqual(user.profile.name, "Provider name")

    def test_email_update_preserves_local_changes_since_lookup(self):
        user = UserFactory(email="original@example.com", profile__name="Original name")
        stale_user = User.all_users.select_related("profile").get(pk=user.pk)
        user.is_active = False
        user.first_name = "Local"
        user.last_name = "Edit"
        user.set_unusable_password()
        user.save()
        user.profile.name = "Locally edited name"
        user.profile.save()
        before = User.all_users.filter(pk=user.pk).values().get()

        updated = self.backend.update_user(
            stale_user, {"email": "changed@example.com", "displayName": "Provider name"}
        )

        self.assertFalse(updated.is_active)
        self.assertEqual(
            User.all_users.filter(pk=user.pk).values().get(),
            {**before, "email": "changed@example.com"},
        )
        self.assertEqual(Profile.all_profiles.get(user=user).name, "Locally edited name")

    def test_update_rechecks_account_type_after_lookup(self):
        user = UserFactory(email="original@example.com", profile__name="Original name")
        stale_user = User.all_users.select_related("profile").get(pk=user.pk)
        user.profile.account_type = Profile.AccountType.SYSTEM
        user.profile.save()
        user_before = User.all_users.filter(pk=user.pk).values().get()
        profile_before = Profile.all_profiles.filter(user=user).values().get()

        with self.assertRaises(SuspiciousOperation):
            self.backend.update_user(
                stale_user, {"email": "changed@example.com", "displayName": "Provider name"}
            )

        self.assertEqual(User.all_users.filter(pk=user.pk).values().get(), user_before)
        self.assertEqual(Profile.all_profiles.filter(user=user).values().get(), profile_before)

    @patch("kitsune.users.auth.update_zendesk_identity.delay")
    def test_identity_sync_waits_for_commit_and_is_discarded_on_rollback(self, sync):
        user = UserFactory(email="original@example.com")
        with self.captureOnCommitCallbacks(execute=True):
            with transaction.atomic():
                self.backend.update_user(user, {"email": "committed@example.com"})
                sync.assert_not_called()
        sync.assert_called_once_with(user.pk, "committed@example.com")
        sync.reset_mock()

        with self.captureOnCommitCallbacks(execute=True):
            with self.assertRaises(RuntimeError), transaction.atomic():
                self.backend.update_user(user, {"email": "rolled-back@example.com"})
                sync.assert_not_called()
                raise RuntimeError("Abort email change")
        sync.assert_not_called()
        user.refresh_from_db()
        self.assertEqual(user.email, "committed@example.com")
