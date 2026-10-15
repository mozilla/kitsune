from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit

import requests
from django.conf import settings
from django.contrib.auth.models import User
from django.core import signing
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import connections, transaction
from django.test import Client, TransactionTestCase, override_settings
from django.utils import timezone
from post_office.models import Email
from pyquery import PyQuery as pq

from kitsune.customercare.models import ZendeskOrganization
from kitsune.customercare.zendesk import ZendeskProvisioningConflict
from kitsune.groups.invitations import (
    INVITATION_ERRORS,
    INVITATION_SALT,
    claim_enterprise_invitation,
    invitation_landing_path,
    issue_enterprise_invitation,
    load_enterprise_invitation,
)
from kitsune.groups.membership import lock_enterprise_hierarchy
from kitsune.groups.models import EnterpriseInvitation, GroupProfile
from kitsune.groups.tests.test_invitations import InvitationFixtures
from kitsune.products.models import SupportOrganization
from kitsune.sumo.tests import TestCase
from kitsune.sumo.urlresolvers import reverse
from kitsune.users.models import Profile
from kitsune.users.tests import UserFactory


@override_settings(
    TESTING=True,
    ENTERPRISE_GROUP_SLUG="claim-enterprise-root",
    ENTERPRISE_ONBOARDING_LANDING_PATH="",
    ENTERPRISE_INVITATION_MAX_AGE=604800,
    READ_ONLY=False,
)
class EnterpriseClaimTests(InvitationFixtures, TestCase):
    def setUp(self):
        super().setUp()
        self.invitation = self.invite()
        self.user = User.all_users.get(pk=self.invitation.user_id)
        ZendeskOrganization.objects.filter(group_profile=self.company).update(zendesk_id="456")
        Profile.all_profiles.filter(user=self.user).update(zendesk_id="123")
        self.user.groups.add(self.company.group)
        self.invitation.status = EnterpriseInvitation.Status.READY
        self.invitation.save(update_fields=["status"])
        self.token = issue_enterprise_invitation(actor=self.actor, invitation=self.invitation)
        self.invitation.refresh_from_db()
        self.claims = {"uid": "authenticated-uid", "email": self.invitation.email}
        self.bind = self.enterContext(
            patch("kitsune.groups.invitations.ZendeskClient.bind_user_identity")
        )

    def assert_rejected_without_changes(self, operation, code):
        before = self.snapshot()
        with self.assertRaises(ValidationError) as raised:
            operation()
        self.assertEqual(raised.exception.code, code)
        self.assertEqual(self.snapshot(), before)

    def assert_claim_rejected(self, code, claims=None):
        self.assert_rejected_without_changes(
            lambda: claim_enterprise_invitation(
                self.token, self.claims if claims is None else claims
            ),
            code,
        )

    def test_issuance_starts_expiry_once_without_mail(self):
        EnterpriseInvitation.objects.filter(pk=self.invitation.pk).update(expires_at=None)
        self.invitation.refresh_from_db()
        before_mail = Email.objects.count()
        before = timezone.now()
        token = issue_enterprise_invitation(actor=self.actor, invitation=self.invitation)
        self.invitation.refresh_from_db()
        expiry = self.invitation.expires_at
        self.assertGreaterEqual(
            expiry, before + timedelta(seconds=settings.ENTERPRISE_INVITATION_MAX_AGE)
        )
        self.assertEqual(load_enterprise_invitation(token).pk, self.invitation.pk)
        issue_enterprise_invitation(actor=self.actor, invitation=self.invitation)
        self.invitation.refresh_from_db()
        self.assertEqual(self.invitation.expires_at, expiry)
        self.assertEqual(Email.objects.count(), before_mail)
        self.assertIsNone(self.invitation.email_queued_at)
        self.bind.assert_not_called()

    def test_issuance_reauthorizes_actor(self):
        outsider = UserFactory(is_staff=True)
        for actor in (outsider, self.user):
            with self.subTest(actor=actor.pk), self.assertRaises(PermissionDenied):
                issue_enterprise_invitation(actor=actor, invitation=self.invitation)

    def test_only_open_invitations_for_prepared_accounts_are_usable(self):
        for fields, code in (
            ({"expires_at": timezone.now() - timedelta(seconds=1)}, "expired_invitation"),
            ({"status": EnterpriseInvitation.Status.PENDING}, "invalid_invitation"),
            ({"status": EnterpriseInvitation.Status.FAILED}, "invalid_invitation"),
            ({"created_user": False}, "invalid_invitation"),
        ):
            with self.subTest(fields=fields), transaction.atomic():
                EnterpriseInvitation.objects.filter(pk=self.invitation.pk).update(**fields)
                for operation in (
                    lambda: issue_enterprise_invitation(
                        actor=self.actor, invitation=self.invitation
                    ),
                    lambda: load_enterprise_invitation(self.token),
                    lambda: claim_enterprise_invitation(self.token, self.claims),
                ):
                    self.assert_rejected_without_changes(operation, code)
                transaction.set_rollback(True)
        self.bind.assert_not_called()

    def test_load_rejects_tampered_or_replaced_tokens(self):
        for token in (
            None,
            "not-a-token",
            self.token + "tampered",
            signing.dumps(
                {"invitation_id": self.invitation.pk, "version": 2}, salt=INVITATION_SALT
            ),
            signing.dumps({"invitation_id": self.invitation.pk, "version": 1}, salt="other"),
        ):
            with self.subTest(token=token), self.assertRaises(ValidationError) as raised:
                load_enterprise_invitation(token)
            self.assertEqual(raised.exception.code, "invalid_invitation")
        EnterpriseInvitation.objects.filter(pk=self.invitation.pk).update(expires_at=None)
        with self.assertRaises(ValidationError) as raised:
            load_enterprise_invitation(self.token)
        self.assertEqual(raised.exception.code, "invalid_invitation")

    def test_claim_activates_prepared_account_and_consumes_link(self):
        users_before = User.all_users.count()
        accepted = claim_enterprise_invitation(self.token, self.claims)
        self.bind.assert_called_once_with(
            zendesk_id="123", fxa_uid=self.claims["uid"], email=self.invitation.email
        )
        self.assertEqual(accepted.pk, self.user.pk)
        self.assertTrue(accepted.is_active)
        self.assertEqual((accepted.first_name, accepted.last_name), ("Jamie", "Rivera"))
        self.assertFalse(accepted.has_usable_password())
        self.assertEqual(accepted.profile.fxa_uid, self.claims["uid"])
        self.assertTrue(accepted.profile.is_fxa_migrated)
        self.assertEqual(User.all_users.count(), users_before)
        self.invitation.refresh_from_db()
        self.assertEqual(self.invitation.status, EnterpriseInvitation.Status.ACCEPTED)
        self.assertIsNotNone(self.invitation.accepted_at)
        self.assertEqual(self.invitation.token_version, 2)
        self.assertFalse(self.root.group.user_set.filter(pk=accepted.pk).exists())
        self.assert_claim_rejected("invalid_invitation")

    def test_maximum_length_captured_names_fit_the_display_name(self):
        # Intake allows 150 characters per name; the display name holds 255.
        User.all_users.filter(pk=self.user.pk).update(first_name="A" * 150, last_name="B" * 150)
        accepted = claim_enterprise_invitation(self.token, self.claims)
        self.assertTrue(accepted.is_active)
        self.assertEqual(accepted.profile.name, "A" * 150 + " " + "B" * 104)

    def test_claim_requires_the_invited_verified_identity(self):
        for claims in (
            {},
            {"uid": "uid"},
            {"email": self.invitation.email},
            {"uid": "  ", "email": self.invitation.email},
            {**self.claims, "email": "other@example.com"},
        ):
            with self.subTest(claims=claims):
                self.assert_claim_rejected("account_mismatch", claims)
        self.bind.assert_not_called()

    def test_claim_refuses_conflicting_accounts(self):
        for name, conflict in (
            ("uid owned elsewhere", lambda: UserFactory(profile__fxa_uid=self.claims["uid"])),
            ("zendesk user owned elsewhere", lambda: UserFactory(profile__zendesk_id="123")),
            ("duplicate email", lambda: UserFactory(email=self.invitation.email.upper())),
            (
                "account already linked",
                lambda: Profile.all_profiles.filter(user=self.user).update(fxa_uid="other-uid"),
            ),
        ):
            with self.subTest(name), transaction.atomic():
                conflict()
                self.assert_claim_rejected("account_conflict")
                transaction.set_rollback(True)
        self.bind.assert_not_called()

    def test_claim_requires_current_company_resources(self):
        for name, change, code in (
            (
                "membership removed",
                lambda: self.user.groups.remove(self.company.group),
                "company_conflict",
            ),
            (
                "public root",
                lambda: GroupProfile.objects.filter(pk=self.root.pk).update(
                    visibility=GroupProfile.Visibility.PUBLIC
                ),
                "configuration_error",
            ),
            (
                "isolation disabled",
                lambda: GroupProfile.objects.filter(pk=self.root.pk).update(
                    isolation_enabled=False
                ),
                "configuration_error",
            ),
            (
                "account deleted",
                lambda: User.all_users.filter(pk=self.user.pk).delete(),
                "resource_missing",
            ),
        ):
            with self.subTest(name), transaction.atomic():
                change()
                self.assert_claim_rejected(code)
                transaction.set_rollback(True)
        self.bind.assert_not_called()

    def test_expected_remote_failures_leave_local_state_unchanged(self):
        for error, code in (
            (requests.Timeout("private provider response"), "zendesk_unavailable"),
            (ZendeskProvisioningConflict("account_conflict"), "account_conflict"),
            (ZendeskProvisioningConflict("zendesk_conflict"), "account_conflict"),
            (ZendeskProvisioningConflict("resource_missing"), "resource_missing"),
        ):
            with self.subTest(code=code):
                self.bind.side_effect = error
                self.assert_claim_rejected(code)

    def test_changes_during_remote_binding_are_detected(self):
        self.bind.side_effect = lambda **kwargs: self.user.groups.remove(self.company.group)
        self.assert_claim_rejected("company_conflict")
        self.bind.side_effect = lambda **kwargs: Profile.all_profiles.filter(
            user=self.user
        ).update(zendesk_id="999")
        self.assert_claim_rejected("account_conflict")

    def test_landing_path_is_server_configured_and_defaults_to_saved_locale(self):
        Profile.all_profiles.filter(user=self.user).update(locale="fr")
        self.assertEqual(
            invitation_landing_path(self.invitation),
            reverse("products.product", kwargs={"slug": self.product.slug}, locale="fr"),
        )
        with self.settings(ENTERPRISE_ONBOARDING_LANDING_PATH="/enterprise/help?source=invite"):
            self.assertEqual(
                invitation_landing_path(self.invitation), "/enterprise/help?source=invite"
            )
        for path in (
            "https://evil.example/",
            "//evil.example/",
            "/\\evil.example/",
            "/bad\npath",
            "relative",
        ):
            with self.subTest(path=path), self.settings(ENTERPRISE_ONBOARDING_LANDING_PATH=path):
                with self.assertRaises(ValidationError) as raised:
                    invitation_landing_path(self.invitation)
                self.assertEqual(raised.exception.code, "configuration_error")

    def test_existing_invitation_group_member_actions_still_work(self):
        self.company.slug = "invitation"
        self.company.save(update_fields=["slug"])
        self.company.leaders.add(self.actor)
        member = UserFactory()
        self.client.force_login(self.actor)

        response = self.client.post(
            reverse("groups.add_member", args=[self.company.slug]),
            {"users": member.username},
        )

        self.assertRedirects(
            response, self.company.get_absolute_url(), fetch_redirect_response=False
        )
        self.assertTrue(self.company.group.user_set.filter(pk=member.pk).exists())

    def test_link_moves_token_to_session_and_previews_invitation(self):
        before = self.snapshot()
        response = self.client.get(reverse("groups.invitation_link", args=[self.token]))
        self.assertRedirects(response, reverse("groups.invitation"), fetch_redirect_response=False)
        self.assertIn("no-store", response["Cache-Control"])

        response = self.client.get(response["Location"])
        self.assertIn("no-store", response["Cache-Control"])
        self.assertContains(response, self.invitation.email)
        self.assertContains(response, self.company.group.name)
        self.assertNotContains(response, self.token)
        sign_in = urlsplit(pq(response.content)("#enterprise-invitation a").attr("href"))
        self.assertEqual(sign_in.path, reverse("users.fxa_authentication_init"))
        self.assertEqual(
            parse_qs(sign_in.query),
            {
                "enterprise_invitation": [str(self.invitation.pk)],
                "next": [invitation_landing_path(self.invitation)],
            },
        )
        self.assertEqual(self.snapshot(), before)
        self.bind.assert_not_called()

    def test_link_rejects_other_methods_without_rendering_a_page(self):
        response = Client(enforce_csrf_checks=True).post(
            reverse("groups.invitation_link", args=[self.token])
        )
        self.assertEqual(response.status_code, 405)
        self.assertEqual(response.content, b"")

    def test_unusable_link_shows_only_an_error(self):
        EnterpriseInvitation.objects.filter(pk=self.invitation.pk).update(
            expires_at=timezone.now() - timedelta(seconds=1)
        )
        for token, code in (
            ("invalid-secret-token", "invalid_invitation"),
            (self.token, "expired_invitation"),
        ):
            with self.subTest(code=code):
                response = self.client.get(
                    reverse("groups.invitation_link", args=[token]), follow=True
                )
                self.assertContains(response, str(INVITATION_ERRORS[code]))
                self.assertNotContains(response, self.invitation.email)
                self.assertNotContains(response, token)
                self.assertFalse(pq(response.content)("#enterprise-invitation a"))


@override_settings(
    TESTING=True,
    ENTERPRISE_GROUP_SLUG="claim-lock-enterprise-root",
    ENTERPRISE_ONBOARDING_LANDING_PATH="",
    ENTERPRISE_INVITATION_MAX_AGE=604800,
    READ_ONLY=False,
)
class EnterpriseClaimLockTests(InvitationFixtures, TransactionTestCase):
    def test_remote_binding_does_not_block_hierarchy_or_resource_row_locks(self):
        invitation = self.invite()
        ZendeskOrganization.objects.filter(group_profile=self.company).update(zendesk_id="456")
        Profile.all_profiles.filter(user_id=invitation.user_id).update(zendesk_id="123")
        invitation.user.groups.add(self.company.group)
        invitation.status = EnterpriseInvitation.Status.READY
        invitation.save(update_fields=["status"])
        token = issue_enterprise_invitation(actor=self.actor, invitation=invitation)

        def lock_resources():
            try:
                with connections["default"].cursor() as cursor:
                    cursor.execute("SET lock_timeout = '2s'")
                with lock_enterprise_hierarchy(exclusive=True):
                    EnterpriseInvitation.objects.select_for_update(nowait=True).get(
                        pk=invitation.pk
                    )
                    GroupProfile.objects.select_for_update(nowait=True).get(pk=self.company.pk)
                    ZendeskOrganization.objects.select_for_update(nowait=True).get(
                        group_profile=self.company
                    )
                    SupportOrganization.objects.select_for_update(nowait=True).get(
                        group=self.company.group
                    )
                    User.all_users.select_for_update(nowait=True).get(pk=invitation.user_id)
                    Profile.all_profiles.select_for_update(nowait=True).get(
                        user_id=invitation.user_id
                    )
            finally:
                connections.close_all()

        def bind_identity(**kwargs):
            with ThreadPoolExecutor(max_workers=1) as pool:
                pool.submit(lock_resources).result(timeout=5)

        with patch(
            "kitsune.groups.invitations.ZendeskClient.bind_user_identity",
            side_effect=bind_identity,
        ):
            accepted = claim_enterprise_invitation(
                token, {"uid": "authenticated-uid", "email": invitation.email}
            )
        self.assertTrue(accepted.is_active)
        invitation.refresh_from_db()
        self.assertEqual(invitation.status, EnterpriseInvitation.Status.ACCEPTED)
