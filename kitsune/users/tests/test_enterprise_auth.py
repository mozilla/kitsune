from datetime import timedelta
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit

from django.contrib.auth.models import AnonymousUser, User
from django.contrib.messages.storage.fallback import FallbackStorage
from django.core.exceptions import SuspiciousOperation
from django.test import RequestFactory, override_settings
from django.utils import timezone
from kombu.exceptions import OperationalError
from requests import Timeout

from kitsune.customercare.models import ZendeskOrganization
from kitsune.customercare.zendesk import ZendeskProvisioningConflict
from kitsune.groups.invitations import invitation_token
from kitsune.groups.models import EnterpriseInvitation
from kitsune.groups.tests.test_invitations import InvitationFixtures
from kitsune.products.tests import ProductFactory
from kitsune.sumo.tests import TestCase
from kitsune.sumo.urlresolvers import reverse
from kitsune.users.auth import FXAAuthBackend
from kitsune.users.models import Profile
from kitsune.users.tests import UserFactory


class EnterpriseAuthFixtures(InvitationFixtures):
    def setUp(self):
        super().setUp()
        self.backend = FXAAuthBackend()
        self.backend.request = RequestFactory().get("/")
        self.backend.request.session = {}
        self.backend.request.user = AnonymousUser()
        self.backend.request._messages = FallbackStorage(self.backend.request)
        self.zendesk = self.enterContext(
            patch("kitsune.groups.invitations.ZendeskClient", autospec=True)
        ).return_value

    def prepared_invitation(self, **kwargs):
        invitation = self.invite(**kwargs)
        Profile.all_profiles.filter(user_id=invitation.user_id).update(
            zendesk_id=str(200 + invitation.pk)
        )
        ZendeskOrganization.objects.filter(group_profile=self.company).update(zendesk_id="101")
        self.company.group.user_set.add(invitation.user)
        invitation.status = EnterpriseInvitation.Status.READY
        invitation.expires_at = timezone.now() + timedelta(days=1)
        invitation.save(update_fields=["status", "expires_at"])
        return invitation, invitation_token(invitation)

    def authenticate_invitation(self, token, claims):
        self.backend.request.enterprise_invitation_token = token
        with patch.object(self.backend, "get_userinfo", return_value=claims):
            return self.backend.get_or_create_user("access", "id", {"sub": "verified"})


@override_settings(
    TESTING=True,
    READ_ONLY=False,
    ENTERPRISE_GROUP_SLUG="auth-enterprise-root",
    ENTERPRISE_ONBOARDING_LANDING_PATH="",
    ENTERPRISE_INVITATION_MAX_AGE=604800,
    FXA_RP_SCOPES="openid email",
)
class EnterpriseInvitationAuthTests(EnterpriseAuthFixtures, TestCase):
    def test_claim_populates_prepared_account_and_normal_login_reuses_it(self):
        invitation, token = self.prepared_invitation()
        product = ProductFactory(codename="invited-subscription")
        self.backend.refresh_token = "saved-refresh-token"
        claims = {
            "email": invitation.email,
            "uid": "authenticated-invitee",
            "avatar": "https://example.com/avatar.png",
            "displayName": "Mozilla display name",
            "locale": "de,en-US",
            "subscriptions": [product.codename],
        }
        users_before = User.all_users.count()
        user = self.authenticate_invitation(token, claims)
        self.assertEqual(user.pk, invitation.user_id)
        self.assertEqual(User.all_users.count(), users_before)
        self.assertEqual((user.first_name, user.last_name), ("Jamie", "Rivera"))
        self.assertTrue(user.is_active)
        self.assertFalse(user.has_usable_password())
        self.assertEqual(user.profile.fxa_uid, claims["uid"])
        self.assertTrue(user.profile.is_fxa_migrated)
        self.assertEqual(user.profile.fxa_refresh_token, "saved-refresh-token")
        self.assertEqual(user.profile.fxa_avatar, claims["avatar"])
        # The captured name, not Mozilla's, keeps the provisioned Zendesk name on sync.
        self.assertEqual(user.profile.name, "Jamie Rivera")
        self.assertEqual(user.profile.locale, "de")
        self.assertEqual(list(user.profile.products.all()), [product])
        invitation.refresh_from_db()
        self.assertEqual(invitation.status, EnterpriseInvitation.Status.ACCEPTED)

        del self.backend.request.enterprise_invitation_token
        with patch.object(self.backend, "get_userinfo", return_value=claims):
            signed_in = self.backend.get_or_create_user("access", "id", {})
        self.assertEqual(signed_in.pk, user.pk)
        self.assertEqual(User.all_users.count(), users_before)
        before = self.snapshot()
        self.assertIsNone(self.authenticate_invitation(token, claims))
        self.assertEqual(self.snapshot(), before)

    def test_unsupported_locale_keeps_saved_locale(self):
        invitation, token = self.prepared_invitation()
        locale = invitation.user.profile.locale
        user = self.authenticate_invitation(
            token, {"email": invitation.email, "uid": "real-uid", "locale": "unsupported"}
        )
        self.assertEqual(user.profile.locale, locale)

    def test_claim_verification_precedes_claiming(self):
        _, token = self.prepared_invitation()
        before = self.snapshot()
        with self.assertRaises(SuspiciousOperation):
            self.authenticate_invitation(token, {"uid": "real-uid"})
        self.assertEqual(self.snapshot(), before)
        self.zendesk.bind_user_identity.assert_not_called()

    def test_remote_identity_conflict_does_not_populate_profile(self):
        invitation, token = self.prepared_invitation()
        self.zendesk.bind_user_identity.side_effect = ZendeskProvisioningConflict(
            "account_conflict"
        )
        before = self.snapshot()
        self.assertIsNone(
            self.authenticate_invitation(
                token,
                {"email": invitation.email, "uid": "real-uid", "displayName": "Not saved"},
            )
        )
        self.assertEqual(self.snapshot(), before)
        self.assertEqual(self.backend.request.enterprise_invitation_error, "account_conflict")

    def test_profile_update_refusal_rolls_back_acceptance_and_can_be_replayed(self):
        invitation, token = self.prepared_invitation()
        claims = {"email": invitation.email, "uid": "real-uid"}
        before = self.snapshot()
        with patch.object(self.backend, "update_user", return_value=None):
            self.assertIsNone(self.authenticate_invitation(token, claims))
        self.assertEqual(self.snapshot(), before)
        self.assertEqual(self.authenticate_invitation(token, claims).pk, invitation.user_id)


@override_settings(
    TESTING=True,
    READ_ONLY=False,
    ENTERPRISE_GROUP_SLUG="oidc-enterprise-root",
    ENTERPRISE_ONBOARDING_LANDING_PATH="/enterprise-support/",
    ENTERPRISE_INVITATION_MAX_AGE=604800,
    FXA_OP_AUTHORIZATION_ENDPOINT="https://accounts.example.com/authorize",
    FXA_RP_SCOPES="openid email",
    FXA_USE_NONCE=True,
    OIDC_USE_PKCE=True,
    AUTHENTICATION_BACKENDS=["kitsune.users.auth.FXAAuthBackend"],
)
class EnterpriseInvitationOIDCTests(EnterpriseAuthFixtures, TestCase):
    def setUp(self):
        super().setUp()
        self.userinfo = self.enterContext(patch.object(FXAAuthBackend, "get_userinfo"))
        self.token_endpoint = self.enterContext(
            patch.object(
                FXAAuthBackend,
                "get_token",
                return_value={"access_token": "access", "id_token": "id"},
            )
        )
        self.enterContext(
            patch.object(FXAAuthBackend, "verify_token", return_value={"sub": "verified"})
        )

    def initiate(self, invitation, token, **params):
        session = self.client.session
        session["enterprise_invitation_token"] = token
        session.save()
        return self.client.get(
            reverse("users.fxa_authentication_init"),
            {"enterprise_invitation": invitation.pk, **params},
        )

    def state_of(self, response):
        return parse_qs(urlsplit(response.url).query)["state"][0]

    def callback(self, state, **params):
        return self.client.get(
            reverse("users.fxa_authentication_callback"),
            {"state": state, "code": "authorization-code", **params},
        )

    def test_initiation_binds_token_to_state_without_disclosing_it_to_provider(self):
        invitation, token = self.prepared_invitation()
        session = self.client.session
        session["enterprise_invitation_states"] = {"removed-state": "old-token"}
        session.save()
        response = self.initiate(invitation, token, next="/enterprise-support/")
        params = parse_qs(urlsplit(response.url).query)
        self.assertEqual(urlsplit(response.url).hostname, "accounts.example.com")
        self.assertNotIn(token, response.url)
        self.assertNotIn("enterprise_invitation", params)
        session = self.client.session
        self.assertEqual(session["enterprise_invitation_states"], {params["state"][0]: token})
        self.assertEqual(session["oidc_login_next"], "/enterprise-support/")

    def test_invalid_or_replaced_pending_token_returns_to_invitation(self):
        invitation, token = self.prepared_invitation()
        for pending_token, invitation_id in ((None, invitation.pk), (token, invitation.pk + 1)):
            with self.subTest(token=pending_token, invitation_id=invitation_id):
                session = self.client.session
                session["enterprise_invitation_token"] = pending_token
                session.save()
                response = self.client.get(
                    reverse("users.fxa_authentication_init"),
                    {"enterprise_invitation": invitation_id},
                )
                self.assertRedirects(
                    response, reverse("groups.invitation"), fetch_redirect_response=False
                )
                self.assertEqual(
                    self.client.session["enterprise_invitation_error"], "invalid_invitation"
                )
                self.token_endpoint.assert_not_called()

    def test_callback_accepts_invitation_even_if_sync_queueing_fails(self):
        invitation, token = self.prepared_invitation()
        state = self.state_of(self.initiate(invitation, token, next="/enterprise-support/"))
        self.userinfo.return_value = {"email": invitation.email.upper(), "uid": "real-uid"}
        with (
            patch(
                "kitsune.users.auth.update_zendesk_identity.delay",
                side_effect=OperationalError("broker unavailable"),
            ),
            patch(
                "kitsune.customercare.signals.update_zendesk_user.delay",
                side_effect=OperationalError("broker unavailable"),
            ),
            self.captureOnCommitCallbacks(execute=True),
        ):
            response = self.callback(state)
        self.assertRedirects(response, "/enterprise-support/", fetch_redirect_response=False)
        invitation.refresh_from_db()
        self.assertEqual(invitation.status, EnterpriseInvitation.Status.ACCEPTED)
        self.assertTrue(User.all_users.get(pk=invitation.user_id).is_active)
        self.assertEqual(self.client.session["_auth_user_id"], str(invitation.user_id))

    def test_verified_invitee_replaces_a_different_signed_in_account(self):
        invitation, token = self.prepared_invitation()
        self.client.force_login(UserFactory())
        state = self.state_of(self.initiate(invitation, token))
        self.userinfo.return_value = {"email": invitation.email, "uid": "real-uid"}
        self.callback(state)
        self.assertEqual(self.client.session["_auth_user_id"], str(invitation.user_id))

    def test_ordinary_sign_in_does_not_claim_a_pending_invitation(self):
        invitation, token = self.prepared_invitation()
        ordinary = UserFactory(email="ordinary@example.com", profile__fxa_uid="ordinary-uid")
        ordinary_state = self.state_of(self.client.get(reverse("users.fxa_authentication_init")))
        invited_state = self.state_of(self.initiate(invitation, token))
        self.userinfo.return_value = {"email": ordinary.email, "uid": "ordinary-uid"}
        self.callback(ordinary_state)
        self.assertEqual(self.client.session["_auth_user_id"], str(ordinary.pk))
        self.assertIn(invited_state, self.client.session["enterprise_invitation_states"])
        self.zendesk.bind_user_identity.assert_not_called()
        invitation.refresh_from_db()
        self.assertEqual(invitation.status, EnterpriseInvitation.Status.READY)

    def test_provider_error_returns_to_invitation(self):
        invitation, token = self.prepared_invitation()
        state = self.state_of(self.initiate(invitation, token))
        response = self.callback(state, error="access_denied")
        self.assertRedirects(response, reverse("groups.invitation"), fetch_redirect_response=False)
        session = self.client.session
        self.assertEqual(session["enterprise_invitation_token"], token)
        self.assertNotIn(state, session["enterprise_invitation_states"])
        self.assertNotIn("enterprise_invitation_error", session)
        self.token_endpoint.assert_not_called()

    def test_remote_failure_returns_to_invitation_without_accepting(self):
        invitation, token = self.prepared_invitation()
        state = self.state_of(self.initiate(invitation, token))
        self.userinfo.return_value = {"email": invitation.email, "uid": "real-uid"}
        self.zendesk.bind_user_identity.side_effect = Timeout("private provider response")
        before = self.snapshot()
        response = self.callback(state)
        self.assertRedirects(response, reverse("groups.invitation"), fetch_redirect_response=False)
        self.assertEqual(self.snapshot(), before)
        session = self.client.session
        self.assertEqual(session["enterprise_invitation_token"], token)
        self.assertEqual(session["enterprise_invitation_error"], "zendesk_unavailable")
        self.assertNotIn("_auth_user_id", session)
