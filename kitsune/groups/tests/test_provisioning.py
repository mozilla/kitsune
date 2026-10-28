import re
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from queue import Queue
from threading import Barrier, Event
from time import monotonic
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit
from uuid import uuid4

import psycopg
import requests
from django.contrib.auth.models import AnonymousUser, User
from django.core import mail
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import connections, transaction
from django.http import Http404
from django.test import Client, TransactionTestCase, override_settings
from django.utils import timezone
from kombu.exceptions import OperationalError
from post_office.models import STATUS, Email
from pyquery import PyQuery as pq
from waffle.testutils import override_switch
from zenpy.lib.exception import APIException, RatelimitBudgetExceeded

from kitsune.customercare.models import ZendeskOrganization
from kitsune.customercare.zendesk import ZendeskProvisioningConflict
from kitsune.groups.invitations import (
    invitation_landing_path,
    invitation_token,
    load_enterprise_invitation,
)
from kitsune.groups.models import EnterpriseInvitation, GroupProfile
from kitsune.groups.provisioning import provision_enterprise_invitation
from kitsune.groups.tests import GroupProfileFactory
from kitsune.groups.tests.test_invitations import InvitationFixtures
from kitsune.groups.views import INVITATION_FAILURES
from kitsune.products.tests import (
    ProductFactory,
    SupportContractFactory,
    SupportCoverageFactory,
)
from kitsune.sumo.tests import TestCase
from kitsune.sumo.urlresolvers import reverse
from kitsune.users.models import Profile
from kitsune.users.tests import GroupFactory, UserFactory


class ProvisioningFixtures(InvitationFixtures):
    def setUp(self):
        super().setUp()
        self.client_class = self.enterContext(
            patch("kitsune.groups.provisioning.ZendeskClient", autospec=True)
        )
        self.client = self.client_class.return_value
        self.client.ensure_organization.return_value = "101"
        self.client.ensure_user.return_value = "201"
        self.client.get_organization_memberships.return_value = []

    def provision(self, invitation, **kwargs):
        return provision_enterprise_invitation(
            actor=kwargs.get("actor", self.actor), invitation=invitation
        )

    def assert_provision_rejected(
        self, invitation, code=None, exception=ValidationError, **kwargs
    ):
        before = self.snapshot()
        self.client_class.reset_mock()
        with self.assertRaises(exception) as raised:
            self.provision(invitation, **kwargs)
        self.client_class.assert_not_called()
        self.assertEqual(self.snapshot(), before)
        if code:
            self.assertEqual(raised.exception.code, code)

    def welcome(self, invitation):
        """Return the queued welcome and the link it asks the invitee to open."""
        email = Email.objects.get(pk=invitation.welcome_email_id)
        return email, re.search(r"https://\S+", email.message).group(0)


@override_settings(
    TESTING=True,
    ENTERPRISE_GROUP_SLUG="provisioning-enterprise-root",
    ENTERPRISE_ONBOARDING_LANDING_PATH="",
    ENTERPRISE_INVITATION_MAX_AGE=604800,
    READ_ONLY=False,
)
class EnterpriseProvisioningTests(ProvisioningFixtures, TestCase):
    def test_prepared_account_gets_membership_and_one_secure_welcome_without_activation(self):
        invitation = self.invite()
        before_user = User.all_users.filter(pk=invitation.user_id).values().get()
        before_profile = Profile.all_profiles.filter(user_id=invitation.user_id).values().get()
        outbox_before = len(mail.outbox)
        mapping = ZendeskOrganization.objects.get(group_profile=self.company)
        # Publishing fails, yet the welcome stays queued for the scheduled delivery run.
        self.send_queued_mail.side_effect = OperationalError("broker unavailable")
        with (
            patch("kitsune.customercare.signals.update_zendesk_user.delay") as sync,
            self.captureOnCommitCallbacks(execute=True),
        ):
            result = self.provision(invitation)
        self.send_queued_mail.assert_called_once_with()
        self.assertEqual(result.status, EnterpriseInvitation.Status.READY)
        self.assertEqual((result.failed_action, result.error_code), ("", ""))
        self.assertEqual(self.client.ensure_user.call_args.kwargs["name"], "Jamie Rivera")
        self.client.remove_organization_memberships.assert_called_once_with(
            user_id="201", organization_ids=set(), memberships=[]
        )
        self.sync_membership.assert_called_once_with(invitation.user_id)
        self.assertEqual(User.all_users.filter(pk=invitation.user_id).values().get(), before_user)
        self.assertEqual(
            Profile.all_profiles.filter(user_id=invitation.user_id).values().get(),
            {**before_profile, "zendesk_id": "201"},
        )
        mapping.refresh_from_db()
        self.assertEqual(mapping.zendesk_id, "101")
        self.assertEqual(
            list(
                User.groups.through.objects.filter(user_id=invitation.user_id).values_list(
                    "group_id", flat=True
                )
            ),
            [self.company.group_id],
        )
        self.assertFalse(GroupProfile.objects.filter(leaders=invitation.user_id).exists())
        self.assertIsNone(result.accepted_at)
        sync.assert_not_called()
        self.assertEqual(len(mail.outbox), outbox_before)
        email, link = self.welcome(result)
        self.assertEqual((email.to, email.status), ([invitation.email], STATUS.queued))
        self.assertIsNotNone(result.email_queued_at)
        self.assertGreater(result.expires_at, timezone.now() + timedelta(days=6))
        self.assertEqual(email.expires_at, result.expires_at)
        self.assertIn(self.company.group.name, email.message)
        self.assertIn(link, email.html_message)
        token = urlsplit(link).path.rsplit("/", 1)[1]
        self.assertEqual(load_enterprise_invitation(token).pk, invitation.pk)

    def test_existing_identity_uses_public_name_and_preserves_account_fields(self):
        user = self.eligible_user(
            profile__name="Current public name",
            profile__locale="de",
            profile__zendesk_id="201",
            profile__public_email=True,
        )
        invitation = self.invite(first_name="Ignored", last_name="Replacement")
        mapping = ZendeskOrganization.objects.get(group_profile=self.company)
        mapping.zendesk_id = "101"
        mapping.save(update_fields=["zendesk_id"])
        before_user = User.all_users.filter(pk=user.pk).values().get()
        before_profile = Profile.all_profiles.filter(user=user).values().get()
        self.provision(invitation)
        self.assertEqual(self.client.ensure_user.call_args.kwargs["name"], "Current public name")
        self.assertEqual(User.all_users.filter(pk=user.pk).values().get(), before_user)
        self.assertEqual(Profile.all_profiles.filter(user=user).values().get(), before_profile)

    def test_existing_account_invitation_is_completed_by_provisioning(self):
        user = self.eligible_user()
        result = self.provision(self.invite())
        self.assertEqual(result.status, EnterpriseInvitation.Status.ACCEPTED)
        self.assertIsNotNone(result.accepted_at)
        self.assertTrue(self.company.group.user_set.filter(pk=user.pk).exists())
        email, link = self.welcome(result)
        sign_in = urlsplit(link)
        self.assertEqual(sign_in.path, reverse("users.fxa_authentication_init"))
        self.assertEqual(parse_qs(sign_in.query), {"next": [invitation_landing_path(result)]})
        self.assertNotIn("/groups/invitation/", email.message)
        self.assertIsNone(email.expires_at)

        user.groups.remove(self.company.group)
        moved = self.invite(company=self.other_company)
        self.assertEqual(moved.company_id, self.other_company.pk)

    @override_settings(
        ZENDESK_CHAT_WIDGET_KEY="widget",
        ZENDESK_CHAT_SIGNING_KEY_ID="key",
        ZENDESK_CHAT_SIGNING_SECRET="secret",
    )
    def test_welcome_lists_covered_products_shared_history_and_chat(self):
        tickets = "Open support tickets for Thunderbird, VPN with Mozilla support agents"
        history = f"See support tickets opened by others at {self.company.group.name}"
        chat = "Chat live with a support agent"
        for name, covered, includes_chat, chat_switch, expected in (
            ("no coverage", False, False, True, {history}),
            ("bundle", True, False, True, {tickets, history}),
            ("bundle with chat", True, True, True, {tickets, history, chat}),
            ("chat switched off", True, True, False, {tickets, history}),
        ):
            with (
                self.subTest(name),
                override_switch("zendesk-chat", active=chat_switch),
                transaction.atomic(),
            ):
                if covered:
                    contract = SupportContractFactory(company=self.company)
                    for order, title in enumerate(("Thunderbird", "VPN")):
                        SupportCoverageFactory(
                            contract=contract,
                            product=ProductFactory(title=title, display_order=order),
                            includes_chat=includes_chat and order == 0,
                        )
                email, _link = self.welcome(self.provision(self.invite()))
                for message in (email.message, email.html_message):
                    self.assertEqual(
                        {line for line in (tickets, history, chat) if line in message}, expected
                    )
                transaction.set_rollback(True)

    def test_provider_failures_keep_saved_ids_and_full_retry_reuses_them(self):
        operations = (
            (
                "ensure_organization",
                "zendesk_organization",
                requests.Timeout("private provider response"),
            ),
            ("ensure_user", "zendesk_user", APIException("private provider response")),
            (
                "ensure_organization_membership",
                "zendesk_membership",
                RatelimitBudgetExceeded("private provider response"),
            ),
            (
                "get_organization_memberships",
                "zendesk_membership",
                requests.Timeout("private provider response"),
            ),
        )
        for index, (method, action, error) in enumerate(operations, start=1):
            with self.subTest(action=action, error=type(error).__name__):
                self.client.reset_mock(side_effect=True)
                invitation = self.invite(email=f"failure-{index}@example.com")
                ZendeskOrganization.objects.filter(group_profile=self.company).update(
                    zendesk_id=None
                )
                user_id = str(200 + invitation.pk)
                self.client.ensure_user.return_value = user_id
                getattr(self.client, method).side_effect = error
                failed = self.provision(invitation)
                failed.refresh_from_db()
                self.assertEqual(failed.status, EnterpriseInvitation.Status.FAILED)
                self.assertEqual(failed.failed_action, action)
                self.assertEqual(failed.error_code, "zendesk_unavailable")
                organization_id = "101" if index > 1 else None
                saved_user_id = user_id if index >= 3 else ""
                self.assertEqual(
                    ZendeskOrganization.objects.get(group_profile=self.company).zendesk_id,
                    organization_id,
                )
                self.assertEqual(
                    Profile.all_profiles.get(user_id=failed.user_id).zendesk_id, saved_user_id
                )
                self.assertFalse(
                    User.groups.through.objects.filter(user_id=failed.user_id).exists()
                )
                self.assertIsNone(failed.welcome_email_id)
                self.client.reset_mock(side_effect=True)
                # Reload persisted state even when the caller still holds a PENDING invitation.
                ready = self.provision(invitation)
                self.assertEqual(ready.status, EnterpriseInvitation.Status.READY)
                self.assertEqual((ready.failed_action, ready.error_code), ("", ""))
                self.assertTrue(
                    User.groups.through.objects.filter(
                        user_id=ready.user_id, group_id=self.company.group_id
                    ).exists()
                )
                self.assertIsNotNone(ready.welcome_email_id)
                self.assertEqual(
                    self.client.ensure_organization.call_args.kwargs["zendesk_id"],
                    organization_id,
                )
                self.assertEqual(
                    self.client.ensure_user.call_args.kwargs["zendesk_id"], saved_user_id or None
                )
                self.client.ensure_organization_membership.assert_called_with(
                    user_id=user_id, organization_id="101", memberships=[]
                )

    def test_unknown_conflict_records_safe_code_and_keeps_prior_work(self):
        invitation = self.invite()
        self.client.ensure_organization_membership.side_effect = ZendeskProvisioningConflict(
            "private remote response with an email or token"
        )
        failed = self.provision(invitation)
        self.assertEqual(failed.status, EnterpriseInvitation.Status.FAILED)
        self.assertEqual(failed.failed_action, "zendesk_membership")
        self.assertEqual(failed.error_code, "zendesk_conflict")
        self.assertEqual(Profile.all_profiles.get(user_id=failed.user_id).zendesk_id, "201")
        self.client.ensure_organization_membership.side_effect = None
        ready = self.provision(invitation)
        self.assertEqual(ready.status, EnterpriseInvitation.Status.READY)
        self.assertEqual((ready.failed_action, ready.error_code), ("", ""))
        self.assertEqual(self.client.ensure_organization.call_args.kwargs["zendesk_id"], "101")
        self.assertEqual(self.client.ensure_user.call_args.kwargs["zendesk_id"], "201")
        self.client.ensure_organization_membership.assert_called_with(
            user_id="201", organization_id="101", memberships=[]
        )

    def test_unexpected_failure_rolls_back_local_changes_and_retry_reruns_operations(self):
        invitation = self.invite()
        mapping = ZendeskOrganization.objects.get(group_profile=self.company)
        before = self.snapshot()
        self.client.ensure_organization_membership.side_effect = RuntimeError("unexpected bug")
        with self.assertRaisesRegex(RuntimeError, "unexpected bug"):
            self.provision(invitation)
        invitation.refresh_from_db()
        mapping.refresh_from_db()
        self.assertEqual(invitation.status, EnterpriseInvitation.Status.PENDING)
        self.assertIsNone(mapping.zendesk_id)
        self.assertEqual(Profile.all_profiles.get(user_id=invitation.user_id).zendesk_id, "")
        self.assertEqual(self.snapshot(), before)
        self.client.reset_mock(side_effect=True)
        ready = self.provision(invitation)
        self.assertEqual(ready.status, EnterpriseInvitation.Status.READY)
        self.assertIsNone(self.client.ensure_organization.call_args.kwargs["zendesk_id"])
        self.assertIsNone(self.client.ensure_user.call_args.kwargs["zendesk_id"])
        self.client.ensure_organization_membership.assert_called_with(
            user_id="201", organization_id="101", memberships=[]
        )

    def test_ready_reconciles_using_fresh_invitation_state_and_clears_stale_errors(self):
        invitation = self.invite()
        self.provision(invitation)
        before = self.snapshot()
        invitation.company = self.other_company
        invitation.user = self.actor
        invitation.email = "stale-caller@example.com"
        EnterpriseInvitation.objects.filter(pk=invitation.pk).update(
            failed_action="zendesk_membership", error_code="zendesk_unavailable"
        )
        self.client_class.reset_mock()
        ready = self.provision(invitation)
        self.assertEqual(ready.status, EnterpriseInvitation.Status.READY)
        self.assertEqual(ready.company_id, self.company.pk)
        self.assertEqual((ready.failed_action, ready.error_code), ("", ""))
        self.assertEqual(self.client.ensure_organization.call_args.kwargs["zendesk_id"], "101")
        self.assertEqual(self.client.ensure_user.call_args.kwargs["zendesk_id"], "201")
        self.client.ensure_organization_membership.assert_called_with(
            user_id="201", organization_id="101", memberships=[]
        )
        self.assertEqual(self.snapshot(), before)

    def test_rerun_welcomes_a_ready_invitation_provisioned_before_welcomes_existed(self):
        invitation = self.invite()
        self.provision(invitation)
        Email.objects.all().delete()
        EnterpriseInvitation.objects.filter(pk=invitation.pk).update(
            welcome_email=None, email_queued_at=None, expires_at=None
        )
        invitation.user.groups.remove(self.company.group)
        ready = self.provision(invitation)
        self.assertEqual(ready.status, EnterpriseInvitation.Status.READY)
        self.assertTrue(self.company.group.user_set.filter(pk=invitation.user_id).exists())
        _email, link = self.welcome(ready)
        token = urlsplit(link).path.rsplit("/", 1)[1]
        self.assertEqual(load_enterprise_invitation(token).pk, invitation.pk)

    def test_skip_ready_uses_fresh_state_when_the_caller_saw_pending(self):
        # A double-submitted request read the invitation before the first one finished it.
        stale = self.invite()
        self.provision(stale)
        self.assertEqual(stale.status, EnterpriseInvitation.Status.PENDING)
        before = self.snapshot()
        self.client_class.reset_mock()
        self.client.ensure_user.side_effect = requests.Timeout("Zendesk is down")
        result = provision_enterprise_invitation(
            actor=self.actor, invitation=stale, skip_ready=True
        )
        self.assertEqual(result.status, EnterpriseInvitation.Status.READY)
        self.assertEqual(self.snapshot(), before)
        self.client_class.assert_not_called()

    def test_accepted_history_is_immutable_even_after_prepared_resources_disappear(self):
        invitation = self.invite()
        EnterpriseInvitation.objects.filter(pk=invitation.pk).update(
            status=EnterpriseInvitation.Status.ACCEPTED,
            accepted_at=timezone.now(),
            user=None,
            failed_action="historic-failure",
            error_code="historic-code",
        )
        ZendeskOrganization.objects.filter(group_profile=self.company).delete()
        staff_without_leadership = UserFactory(is_staff=True)
        before = self.snapshot()
        with (
            patch(
                "kitsune.groups.provisioning.lock_enterprise_hierarchy",
                side_effect=AssertionError("Accepted history must not lock the hierarchy"),
            ),
            patch(
                "django.db.models.query.QuerySet.select_for_update",
                side_effect=AssertionError("Accepted history must not lock rows"),
            ),
        ):
            accepted = self.provision(invitation)
            self.assertEqual(accepted.status, EnterpriseInvitation.Status.ACCEPTED)
            self.assertEqual(self.snapshot(), before)
            self.client_class.assert_not_called()
            self.assert_provision_rejected(
                invitation, actor=AnonymousUser(), exception=PermissionDenied
            )
            self.assert_provision_rejected(
                invitation, actor=staff_without_leadership, exception=PermissionDenied
            )
            with override_settings(READ_ONLY=True):
                self.assert_provision_rejected(invitation, exception=PermissionDenied)

    def test_only_active_staff_with_root_moderation_can_provision(self):
        invitation = self.invite()
        leader = UserFactory()
        inactive = UserFactory(is_staff=True, is_active=False)
        company_leader = UserFactory(is_staff=True)
        member = UserFactory(is_staff=True)
        self.root.leaders.add(leader, inactive)
        self.company.leaders.add(company_leader)
        member.groups.add(self.root.group)
        for actor in (
            AnonymousUser(),
            leader,
            inactive,
            company_leader,
            member,
            UserFactory(is_staff=True),
        ):
            with self.subTest(actor=actor):
                self.assert_provision_rejected(invitation, actor=actor, exception=PermissionDenied)
        with override_settings(READ_ONLY=True):
            self.assert_provision_rejected(invitation, exception=PermissionDenied)

    def test_actor_permission_changes_are_not_hidden_by_cached_user(self):
        invitation = self.invite()
        for field in ("is_staff", "is_active"):
            with self.subTest(field=field):
                User.all_users.filter(pk=self.actor.pk).update(**{field: False})
                self.assert_provision_rejected(invitation, exception=PermissionDenied)
                User.all_users.filter(pk=self.actor.pk).update(**{field: True})
        self.root.leaders.remove(self.actor)
        self.assert_provision_rejected(invitation, exception=PermissionDenied)

    def test_root_and_company_hierarchy_drift_prevents_provider_calls(self):
        invitation = self.invite()
        with override_settings(ENTERPRISE_GROUP_SLUG="missing-root"):
            self.assert_provision_rejected(invitation, code="configuration_error")
        for changes in (
            {"visibility": GroupProfile.Visibility.PUBLIC},
            {"isolation_enabled": False},
        ):
            with self.subTest(changes=changes):
                GroupProfile.objects.filter(pk=self.root.pk).update(**changes)
                self.assert_provision_rejected(invitation, code="configuration_error")
                GroupProfile.objects.filter(pk=self.root.pk).update(
                    visibility=GroupProfile.Visibility.PRIVATE, isolation_enabled=True
                )
        self.company.move(self.other_company, "last-child")
        self.assert_provision_rejected(invitation, exception=Http404)

    def test_missing_prepared_resources_are_not_recreated(self):
        for name, remove in (
            (
                "mapping",
                lambda invitation: ZendeskOrganization.objects.filter(
                    group_profile=self.company
                ).delete(),
            ),
            (
                "profile",
                lambda invitation: Profile.all_profiles.filter(
                    user_id=invitation.user_id
                ).delete(),
            ),
            ("user", lambda invitation: User.all_users.filter(pk=invitation.user_id).delete()),
        ):
            with self.subTest(name), transaction.atomic():
                invitation = self.invite()
                remove(invitation)
                self.assert_provision_rejected(invitation, code="resource_missing")
                transaction.set_rollback(True)

    def test_duplicate_hidden_email_or_changed_local_email_is_not_rebound(self):
        invitation = self.invite()
        hidden = UserFactory(
            email=invitation.email.upper(), profile__account_type=Profile.AccountType.SYSTEM
        )
        self.assert_provision_rejected(invitation, code="account_conflict")
        hidden.delete()
        User.all_users.filter(pk=invitation.user_id).update(email="changed@example.com")
        self.assert_provision_rejected(invitation, code="account_conflict")

    def test_prepared_account_must_remain_eligible(self):
        user_changes = (
            {"is_active": True},
            {"is_staff": True},
            {"is_superuser": True},
            {"password": "usable-password-hash"},
            {"last_login": timezone.now()},
        )
        profile_changes = (
            {"account_type": Profile.AccountType.SYSTEM},
            {"account_type": Profile.AccountType.ADMIN},
            {"is_fxa_migrated": True},
            {"fxa_uid": "unexpected-identity"},
        )
        for index, changes in enumerate(user_changes):
            with self.subTest(user_changes=changes):
                invitation = self.invite(email=f"user-drift-{index}@example.com")
                User.all_users.filter(pk=invitation.user_id).update(**changes)
                self.assert_provision_rejected(invitation, code="account_conflict")
        for index, changes in enumerate(profile_changes):
            with self.subTest(profile_changes=changes):
                invitation = self.invite(email=f"profile-drift-{index}@example.com")
                Profile.all_profiles.filter(user_id=invitation.user_id).update(**changes)
                self.assert_provision_rejected(invitation, code="account_conflict")

    def test_other_company_membership_is_rechecked(self):
        invitation = self.invite()
        user = User.all_users.get(pk=invitation.user_id)
        department = self.child(self.other_company)
        user.groups.add(department.group)
        self.assert_provision_rejected(invitation, code="company_conflict")

    def test_invalid_remote_ids_are_rejected_before_provider_calls(self):
        invitation = self.invite()
        self.provision(invitation)
        mapping = ZendeskOrganization.objects.get(group_profile=self.company)
        for model, lookup in (
            (ZendeskOrganization, {"pk": mapping.pk}),
            (Profile, {"user_id": invitation.user_id}),
        ):
            manager = model.all_profiles if model is Profile else model.objects
            original_id = manager.get(**lookup).zendesk_id
            for value in ("not-an-id", "0", "-1", "２０１"):
                with self.subTest(model=model.__name__, value=value):
                    manager.filter(**lookup).update(zendesk_id=value)
                    self.assert_provision_rejected(invitation, code="configuration_error")
            manager.filter(**lookup).update(zendesk_id=original_id)

    def test_cleared_remote_links_can_be_reconciled(self):
        for status in (EnterpriseInvitation.Status.FAILED, EnterpriseInvitation.Status.READY):
            with self.subTest(status=status):
                invitation = self.invite(email=f"reconcile-{status}@example.com")
                user_id = str(200 + invitation.pk)
                self.client.ensure_user.return_value = user_id
                if status == EnterpriseInvitation.Status.FAILED:
                    self.client.ensure_organization_membership.side_effect = requests.Timeout()
                self.assertEqual(self.provision(invitation).status, status)
                ZendeskOrganization.objects.filter(group_profile=self.company).update(
                    zendesk_id=None
                )
                Profile.all_profiles.filter(user_id=invitation.user_id).update(zendesk_id="")
                self.client.reset_mock(side_effect=True)
                ready = self.provision(invitation)
                self.assertEqual(ready.status, EnterpriseInvitation.Status.READY)
                self.assertEqual((ready.failed_action, ready.error_code), ("", ""))
                self.assertIsNone(self.client.ensure_organization.call_args.kwargs["zendesk_id"])
                self.assertIsNone(self.client.ensure_user.call_args.kwargs["zendesk_id"])
                self.client.ensure_organization_membership.assert_called_with(
                    user_id=user_id, organization_id="101", memberships=[]
                )
                self.assertEqual(
                    ZendeskOrganization.objects.get(group_profile=self.company).zendesk_id, "101"
                )
                self.assertEqual(
                    Profile.all_profiles.get(user_id=invitation.user_id).zendesk_id, user_id
                )

    def test_hidden_profile_ownership_conflict_preserves_saved_organization_id(self):
        invitation = self.invite()
        owner = UserFactory(
            profile__zendesk_id="201", profile__account_type=Profile.AccountType.SYSTEM
        )
        before_owner = Profile.all_profiles.filter(user=owner).values().get()
        failed = self.provision(invitation)
        self.assertEqual(failed.status, EnterpriseInvitation.Status.FAILED)
        self.assertEqual(
            ZendeskOrganization.objects.get(group_profile=self.company).zendesk_id, "101"
        )
        self.assertEqual(
            (failed.failed_action, failed.error_code), ("zendesk_user", "account_conflict")
        )
        self.assertEqual(Profile.all_profiles.get(user_id=failed.user_id).zendesk_id, "")
        self.assertEqual(Profile.all_profiles.filter(user=owner).values().get(), before_owner)
        self.client.ensure_organization_membership.assert_not_called()
        self.client.reset_mock()
        self.provision(invitation)
        self.assertEqual(self.client.ensure_organization.call_args.kwargs["zendesk_id"], "101")
        self.assertIsNone(self.client.ensure_user.call_args.kwargs["zendesk_id"])
        self.client.ensure_organization_membership.assert_not_called()
        Profile.all_profiles.filter(user=owner).update(zendesk_id="202")
        ready = self.provision(invitation)
        self.assertEqual(ready.status, EnterpriseInvitation.Status.READY)
        self.assertEqual(self.client.ensure_organization.call_args.kwargs["zendesk_id"], "101")
        self.client.ensure_organization_membership.assert_called_with(
            user_id="201", organization_id="101", memberships=[]
        )

    def test_preexisting_duplicate_remote_user_link_rejects_before_provider_calls(self):
        invitation = self.invite()
        Profile.all_profiles.filter(user_id=invitation.user_id).update(zendesk_id="201")
        UserFactory(profile__zendesk_id="201", profile__account_type=Profile.AccountType.SYSTEM)
        self.assert_provision_rejected(invitation, code="account_conflict")

    def test_duplicate_organization_id_uses_savepoint_and_records_safe_failure(self):
        invitation = self.invite()
        owner = ZendeskOrganization.objects.create(
            group_profile=self.other_company, zendesk_id="101"
        )
        failed = self.provision(invitation)
        self.assertEqual(failed.status, EnterpriseInvitation.Status.FAILED)
        self.assertEqual(
            (failed.failed_action, failed.error_code), ("zendesk_organization", "zendesk_conflict")
        )
        self.assertIsNone(ZendeskOrganization.objects.get(group_profile=self.company).zendesk_id)
        owner.refresh_from_db()
        self.assertEqual(owner.zendesk_id, "101")
        self.client.ensure_user.assert_not_called()
        self.client.ensure_organization_membership.assert_not_called()
        # A failed unique write must not leave the outer transaction broken.
        self.assertEqual(
            EnterpriseInvitation.objects.get(pk=failed.pk).error_code, "zendesk_conflict"
        )
        owner.zendesk_id = "102"
        owner.save(update_fields=["zendesk_id"])
        self.client.reset_mock()
        ready = self.provision(invitation)
        self.assertEqual(ready.status, EnterpriseInvitation.Status.READY)
        self.client.ensure_organization.assert_called()

    def test_unexpected_local_failure_rolls_back_remote_links_and_membership(self):
        invitation = self.invite()
        before = self.snapshot()
        for model in (Profile, EnterpriseInvitation):
            with (
                self.subTest(model=model),
                patch.object(model, "save", side_effect=RuntimeError("unexpected local failure")),
                self.assertRaisesRegex(RuntimeError, "unexpected local failure"),
            ):
                self.provision(invitation)
            self.assertEqual(self.snapshot(), before)

    def test_provider_calls_observe_no_local_provisioning_writes(self):
        invitation = self.invite()
        before = self.snapshot()

        def ensure_organization(**kwargs):
            self.assertEqual(self.snapshot(), before)
            return "101"

        def ensure_user(**kwargs):
            self.assertEqual(self.snapshot(), before)
            return "201"

        def ensure_membership(**kwargs):
            self.assertEqual(self.snapshot(), before)

        self.client.ensure_organization.side_effect = ensure_organization
        self.client.ensure_user.side_effect = ensure_user
        self.client.ensure_organization_membership.side_effect = ensure_membership
        ready = self.provision(invitation)
        self.assertEqual(ready.status, EnterpriseInvitation.Status.READY)


@override_settings(
    TESTING=True,
    ES_LIVE_INDEXING=False,
    ENTERPRISE_GROUP_SLUG="provisioning-concurrency-root",
    ENTERPRISE_ONBOARDING_LANDING_PATH="",
    ENTERPRISE_INVITATION_MAX_AGE=604800,
    READ_ONLY=False,
)
class EnterpriseProvisioningConcurrencyTests(ProvisioningFixtures, TransactionTestCase):
    def compete(self, first, second):
        """Prove the contender blocks in PostgreSQL before releasing the first commit."""
        prepared, release = Event(), Event()
        first_pid, second_pid = Queue(), Queue()

        def run(operation, pid_queue, hold):
            connection = connections["default"]
            try:
                with transaction.atomic():
                    with connection.cursor() as cursor:
                        cursor.execute("SET LOCAL statement_timeout = '30s'")
                        cursor.execute("SELECT pg_backend_pid()")
                        pid_queue.put(cursor.fetchone()[0])
                    result = operation()
                    if hold:
                        prepared.set()
                        if not release.wait(25):
                            raise AssertionError("Competing operation never reached its lock")
                return result
            finally:
                connection.close()

        observer_params = connections["default"].get_connection_params()
        observer_params["autocommit"] = True
        connections.close_all()
        with (
            psycopg.connect(**observer_params) as observer,
            ThreadPoolExecutor(max_workers=2) as pool,
        ):
            owner = pool.submit(run, first, first_pid, True)
            try:
                self.assertTrue(
                    prepared.wait(15), "First operation did not prepare its transaction"
                )
                owner_pid = first_pid.get(timeout=5)
                contender = pool.submit(run, second, second_pid, False)
                contender_pid = second_pid.get(timeout=5)
                deadline = monotonic() + 10
                while monotonic() < deadline:
                    with observer.cursor() as cursor:
                        cursor.execute(
                            "SELECT wait_event_type, wait_event, pg_blocking_pids(pid) "
                            "FROM pg_stat_activity WHERE pid = %s",
                            [contender_pid],
                        )
                        state = cursor.fetchone()
                    if state and state[:2] == ("Lock", "advisory") and owner_pid in state[2]:
                        break
                    if contender.done():
                        self.fail(f"Competing operation bypassed the lock: {contender.result()!r}")
                    release.wait(0.01)
                else:
                    self.fail(f"Competing connection did not wait for an advisory lock: {state!r}")
            finally:
                release.set()
            return owner.result(timeout=15), contender.result(timeout=15)

    def test_different_invitees_can_provision_the_same_unlinked_company_concurrently(self):
        invitations = (
            self.invite(email="first-invitee@example.com"),
            self.invite(email="second-invitee@example.com"),
        )
        remote_users = {invitation.email: str(201 + i) for i, invitation in enumerate(invitations)}
        organization_calls = Barrier(2, timeout=10)

        def ensure_organization(**kwargs):
            organization_calls.wait()
            return "101"

        def provision(invitation):
            try:
                return self.provision(invitation)
            finally:
                connections["default"].close()

        self.client.ensure_organization.side_effect = ensure_organization
        self.client.ensure_user.side_effect = lambda email, **kwargs: remote_users[email]
        connections.close_all()
        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [pool.submit(provision, invitation) for invitation in invitations]
            results = [future.result(timeout=15) for future in futures]

        for result in results:
            self.assertEqual(result.status, EnterpriseInvitation.Status.READY)
            self.assertEqual(
                Profile.all_profiles.get(user_id=result.user_id).zendesk_id,
                remote_users[result.email],
            )
        self.assertEqual(
            ZendeskOrganization.objects.get(group_profile=self.company).zendesk_id, "101"
        )

    def test_intake_and_provisioning_share_email_lock_and_account_binding(self):
        invitation = self.invite()
        first, second = self.compete(
            lambda: self.invite(first_name="Do not replace").pk,
            lambda: self.provision(invitation).pk,
        )
        self.assertEqual((first, second), (invitation.pk, invitation.pk))
        invitation.refresh_from_db()
        self.assertEqual(invitation.status, EnterpriseInvitation.Status.READY)
        self.assertEqual(invitation.user.first_name, "Jamie")
        self.assertFalse(invitation.user.is_active)
        self.assertEqual(User.all_users.filter(email__iexact=invitation.email).count(), 1)

    def during_provider_call(
        self, invitation, operation, *, provider="ensure_organization_membership", exception=None
    ):
        """Commit a competing change while the provider is still waiting for its response."""
        entered, release = Event(), Event()
        method = getattr(self.client, provider)
        before = self.snapshot()

        def pause(**kwargs):
            entered.set()
            if not release.wait(25):
                raise AssertionError("The competing operation did not finish during provider I/O")
            return method.return_value

        def run(operation):
            connection = connections["default"]
            try:
                with transaction.atomic():
                    with connection.cursor() as cursor:
                        cursor.execute("SET LOCAL statement_timeout = '20s'")
                    return operation()
            finally:
                connection.close()

        connections.close_all()
        previous_side_effect = method.side_effect
        method.side_effect = pause
        try:
            with ThreadPoolExecutor(max_workers=2) as pool:
                provisioning = pool.submit(run, lambda: self.provision(invitation))
                try:
                    self.assertTrue(entered.wait(15), "Provisioning did not reach the provider")
                    self.assertEqual(
                        self.snapshot(), before, "Provider I/O must precede local writes"
                    )
                    # Return the observer's connection before the second worker needs the pool.
                    connections["default"].close()
                    mutation = pool.submit(run, operation)
                    mutation.result(timeout=10)
                    after_mutation = self.snapshot()
                finally:
                    release.set()
                if exception is not None:
                    with self.assertRaises(exception) as raised:
                        provisioning.result(timeout=15)
                    self.assertEqual(self.snapshot(), after_mutation)
                    return raised.exception
                return provisioning.result(timeout=15)
        finally:
            method.side_effect = previous_side_effect

    def test_company_and_account_rows_stay_writable_through_every_provider_call(self):
        for index, provider in enumerate(
            ("ensure_organization", "ensure_user", "ensure_organization_membership")
        ):
            with self.subTest(provider=provider):
                invitation = self.invite(email=f"unlocked-{index}@example.com")
                self.client.ensure_user.return_value = str(300 + index)
                ZendeskOrganization.objects.filter(group_profile=self.company).update(
                    zendesk_id=None
                )

                def edit_resources():
                    EnterpriseInvitation.objects.select_for_update().get(pk=invitation.pk)
                    GroupProfile.objects.filter(pk=self.company.pk).update(
                        information="Updated during provider I/O"
                    )
                    ZendeskOrganization.objects.select_for_update().get(group_profile=self.company)
                    User.all_users.filter(pk=invitation.user_id).update(first_name="Updated")
                    Profile.all_profiles.filter(user_id=invitation.user_id).update(
                        name="Updated public name", locale="de"
                    )

                ready = self.during_provider_call(invitation, edit_resources, provider=provider)
                self.assertEqual(ready.status, EnterpriseInvitation.Status.READY)
                user = User.all_users.get(pk=invitation.user_id)
                profile = Profile.all_profiles.get(user=user)
                self.assertEqual(user.first_name, "Updated")
                self.assertEqual((profile.name, profile.locale), ("Updated public name", "de"))

    def test_hierarchy_move_completes_during_provider_io_and_stops_stale_writes(self):
        invitation = self.invite()
        destination = GroupProfileFactory()
        self.during_provider_call(
            invitation,
            lambda: self.company.move(destination, "last-child"),
            exception=Http404,
        )
        self.company.refresh_from_db()
        self.assertEqual(self.company.get_parent().pk, destination.pk)
        self.cleanup_membership.assert_called_once_with(invitation.user_id, "201", ("101",))

    def test_permission_revocation_during_provider_io_stops_stale_writes(self):
        for change in ("is_staff", "is_active", "root_leadership"):
            with self.subTest(change=change):
                invitation = self.invite(email=f"permission-{change}@example.com")

                def revoke_permission():
                    if change == "root_leadership":
                        self.root.leaders.remove(self.actor)
                    else:
                        User.all_users.filter(pk=self.actor.pk).update(**{change: False})

                self.during_provider_call(
                    invitation, revoke_permission, exception=PermissionDenied
                )
                User.all_users.filter(pk=self.actor.pk).update(is_staff=True, is_active=True)
                self.root.leaders.add(self.actor)

    def test_company_group_relink_during_provider_io_stops_stale_writes(self):
        invitation = self.invite()
        replacement = GroupFactory()

        def relink_company():
            company = GroupProfile.objects.get(pk=self.company.pk)
            company.group = replacement
            company.save(update_fields=["group"])

        error = self.during_provider_call(invitation, relink_company, exception=ValidationError)
        self.assertEqual(error.code, "account_conflict")

    def test_mapping_relink_during_provider_io_stops_stale_writes(self):
        for change in ("external_id", "zendesk_id", "replacement"):
            with self.subTest(change=change):
                invitation = self.invite(email=f"mapping-{change}@example.com")
                mapping = ZendeskOrganization.objects.get(group_profile=self.company)

                def relink_mapping():
                    if change == "replacement":
                        mapping.delete()
                        ZendeskOrganization.objects.create(group_profile=self.company)
                    else:
                        ZendeskOrganization.objects.filter(pk=mapping.pk).update(
                            **{change: uuid4() if change == "external_id" else "102"}
                        )

                error = self.during_provider_call(
                    invitation, relink_mapping, exception=ValidationError
                )
                self.assertEqual(error.code, "account_conflict")
                ZendeskOrganization.objects.filter(group_profile=self.company).update(
                    zendesk_id=None
                )

    def test_profile_identity_relink_during_provider_io_stops_stale_writes(self):
        for change in ("fxa_uid", "zendesk_id", "replacement"):
            with self.subTest(change=change):
                user = self.eligible_user(
                    email=f"profile-{change}@example.com",
                    profile__fxa_uid=f"original-{change}",
                )
                invitation = self.invite(email=user.email)
                profile = Profile.all_profiles.get(user=user)

                def relink_profile():
                    if change == "replacement":
                        profile.delete()
                        Profile.all_profiles.create(user=user, fxa_uid=f"replacement-{change}")
                    else:
                        Profile.all_profiles.filter(pk=profile.pk).update(
                            **{
                                change: "replacement-fxa-identity"
                                if change == "fxa_uid"
                                else "202"
                            }
                        )

                error = self.during_provider_call(
                    invitation, relink_profile, exception=ValidationError
                )
                self.assertEqual(error.code, "account_conflict")

    def test_matching_remote_user_link_saved_during_provider_io_is_preserved(self):
        invitation = self.invite()
        result = self.during_provider_call(
            invitation,
            lambda: Profile.all_profiles.filter(user_id=invitation.user_id).update(
                zendesk_id="201"
            ),
        )
        self.assertEqual(result.status, EnterpriseInvitation.Status.READY)
        self.assertEqual(Profile.all_profiles.get(user_id=invitation.user_id).zendesk_id, "201")
        self.assertEqual(
            ZendeskOrganization.objects.get(group_profile=self.company).zendesk_id, "101"
        )

    def test_cleared_user_link_is_rejected_when_remote_user_resolution_fails(self):
        invitation = self.invite()
        Profile.all_profiles.filter(user_id=invitation.user_id).update(zendesk_id="201")
        self.client.ensure_user.side_effect = requests.Timeout()
        error = self.during_provider_call(
            invitation,
            lambda: Profile.all_profiles.filter(user_id=invitation.user_id).update(zendesk_id=""),
            provider="ensure_organization",
            exception=ValidationError,
        )
        self.assertEqual(error.code, "account_conflict")

    def test_membership_change_during_provider_io_stops_stale_writes(self):
        invitation = self.invite()
        user = User.all_users.get(pk=invitation.user_id)
        error = self.during_provider_call(
            invitation,
            lambda: user.groups.add(self.other_company.group),
            exception=ValidationError,
        )
        self.assertEqual(error.code, "company_conflict")

    def test_inflight_acceptance_keeps_accepted_history_immutable(self):
        invitation = self.invite()
        accepted_at = timezone.now()
        result = self.during_provider_call(
            invitation,
            lambda: EnterpriseInvitation.objects.filter(pk=invitation.pk).update(
                status=EnterpriseInvitation.Status.ACCEPTED,
                accepted_at=accepted_at,
                user=None,
                failed_action="historic-failure",
                error_code="historic-code",
            ),
        )
        self.assertEqual(result.status, EnterpriseInvitation.Status.ACCEPTED)
        self.assertEqual(result.accepted_at, accepted_at)
        self.assertEqual(
            (result.failed_action, result.error_code), ("historic-failure", "historic-code")
        )
        self.assertIsNone(ZendeskOrganization.objects.get(group_profile=self.company).zendesk_id)
        self.assertEqual(Profile.all_profiles.get(user_id=invitation.user_id).zendesk_id, "")

    def test_new_remote_user_owner_is_rechecked_after_provider_io(self):
        invitation = self.invite()
        owner = UserFactory(profile__account_type=Profile.AccountType.SYSTEM)
        failed = self.during_provider_call(
            invitation,
            lambda: Profile.all_profiles.filter(user=owner).update(zendesk_id="201"),
        )
        self.assertEqual(failed.status, EnterpriseInvitation.Status.FAILED)
        self.assertEqual(
            (failed.failed_action, failed.error_code), ("zendesk_user", "account_conflict")
        )
        self.assertEqual(Profile.all_profiles.get(user_id=invitation.user_id).zendesk_id, "")
        self.assertEqual(
            ZendeskOrganization.objects.get(group_profile=self.company).zendesk_id, "101"
        )

    def test_new_organization_owner_uses_savepoint_and_preserves_valid_user_id(self):
        invitation = self.invite()
        owner = ZendeskOrganization.objects.create(group_profile=self.other_company)
        failed = self.during_provider_call(
            invitation,
            lambda: ZendeskOrganization.objects.filter(pk=owner.pk).update(zendesk_id="101"),
        )
        self.assertEqual(failed.status, EnterpriseInvitation.Status.FAILED)
        self.assertEqual(
            (failed.failed_action, failed.error_code), ("zendesk_organization", "zendesk_conflict")
        )
        self.assertIsNone(ZendeskOrganization.objects.get(group_profile=self.company).zendesk_id)
        self.assertEqual(Profile.all_profiles.get(user_id=invitation.user_id).zendesk_id, "201")
        owner.refresh_from_db()
        self.assertEqual(owner.zendesk_id, "101")


@override_settings(
    TESTING=True,
    ENTERPRISE_GROUP_SLUG="invitation-view-enterprise-root",
    ENTERPRISE_ONBOARDING_LANDING_PATH="",
    ENTERPRISE_INVITATION_MAX_AGE=604800,
    READ_ONLY=False,
)
class EnterpriseInvitationViewTests(ProvisioningFixtures, TestCase):
    def setUp(self):
        super().setUp()
        # ProvisioningFixtures uses self.client for the mocked Zendesk client.
        self.http = Client()
        self.http.force_login(self.actor)
        self.page_url = self.company.get_absolute_url()
        self.invite_url = reverse("groups.invite_user", args=[self.company.slug])
        self.person = {"email": "jamie@example.com", "first_name": "Jamie", "last_name": "Rivera"}

    def resend_url(self, invitation, company=None):
        return reverse(
            "groups.resend_invitation", args=[(company or self.company).slug, invitation.pk]
        )

    def rows(self):
        page = pq(self.http.get(self.page_url).content)
        return [
            (cells.eq(1).text(), cells.eq(2).text())
            for row in page("#enterprise-invitations tbody tr")
            for cells in [pq(row).find("td")]
        ]

    def test_adding_a_person_provisions_and_welcomes_them(self):
        response = self.http.post(self.invite_url, self.person)
        self.assertRedirects(response, self.page_url, fetch_redirect_response=False)
        invitation = EnterpriseInvitation.objects.get(email=self.person["email"])
        self.assertEqual(invitation.company_id, self.company.pk)
        self.assertEqual(invitation.status, EnterpriseInvitation.Status.READY)
        self.assertIsNotNone(invitation.welcome_email_id)
        self.assertEqual(
            self.rows(), [(self.person["email"], str(EnterpriseInvitation.Status.READY.label))]
        )

    def test_adding_an_invited_person_again_leaves_their_invitation_alone(self):
        self.http.post(self.invite_url, self.person)
        invitation = EnterpriseInvitation.objects.get(email=self.person["email"])
        before = (list(EnterpriseInvitation.objects.values()), Email.objects.count())
        self.client_class.reset_mock()
        # Even with Zendesk down, the link they already have must keep working.
        self.client.ensure_user.side_effect = requests.Timeout("Zendesk is down")
        self.http.post(self.invite_url, self.person)
        self.assertEqual(
            load_enterprise_invitation(invitation_token(invitation)).pk, invitation.pk
        )
        self.assertEqual(
            (list(EnterpriseInvitation.objects.values()), Email.objects.count()), before
        )
        self.client_class.assert_not_called()

    def test_resend_finishes_failed_setup_then_sends_a_fresh_link(self):
        self.client.ensure_user.side_effect = requests.Timeout("Zendesk is down")
        self.http.post(self.invite_url, self.person)
        invitation = EnterpriseInvitation.objects.get(email=self.person["email"])
        self.assertEqual(invitation.status, EnterpriseInvitation.Status.FAILED)
        self.assertIsNone(invitation.welcome_email_id)
        # The reason stays visible after the flash message is gone.
        self.assertIn(str(INVITATION_FAILURES["zendesk_unavailable"]), self.rows()[0][1])

        self.client.ensure_user.side_effect = None
        response = self.http.post(self.resend_url(invitation))
        self.assertRedirects(response, self.page_url, fetch_redirect_response=False)
        invitation.refresh_from_db()
        self.assertEqual(invitation.status, EnterpriseInvitation.Status.READY)
        first_welcome = invitation.welcome_email_id
        self.assertIsNotNone(first_welcome)

        self.http.post(self.resend_url(invitation))
        invitation.refresh_from_db()
        self.assertEqual(invitation.token_version, 2)
        self.assertNotEqual(invitation.welcome_email_id, first_welcome)

    def test_resend_reports_an_unsendable_welcome_and_changes_nothing(self):
        self.http.post(self.invite_url, self.person)
        invitation = EnterpriseInvitation.objects.get(email=self.person["email"])
        before = (list(EnterpriseInvitation.objects.values()), Email.objects.count())
        # post-office rejects the sender with a field-error dict that carries no code.
        with override_settings(DEFAULT_FROM_EMAIL="not-an-address"):
            response = self.http.post(self.resend_url(invitation))
        self.assertRedirects(response, self.page_url, fetch_redirect_response=False)
        self.assertEqual(
            (list(EnterpriseInvitation.objects.values()), Email.objects.count()), before
        )

    def test_accepted_people_leave_the_list_and_a_stale_resend_is_harmless(self):
        self.eligible_user(email="existing@example.com")
        self.http.post(self.invite_url, {**self.person, "email": "existing@example.com"})
        invitation = EnterpriseInvitation.objects.get(email="existing@example.com")
        self.assertEqual(invitation.status, EnterpriseInvitation.Status.ACCEPTED)
        self.assertEqual(self.rows(), [])
        before = self.snapshot()
        self.client_class.reset_mock()
        self.http.post(self.resend_url(invitation))
        self.assertEqual(self.snapshot(), before)
        self.client_class.assert_not_called()

    def test_invalid_input_is_redisplayed_without_creating_anything(self):
        before = self.snapshot()
        response = self.http.post(self.invite_url, {**self.person, "last_name": "  "})
        self.assertEqual(response.status_code, 200)
        form = pq(response.content)("#enterprise-invite-form")
        self.assertEqual(form.find("#id_email").val(), self.person["email"])
        self.assertEqual(len(form.find(".has-error")), 1)
        self.assertEqual(self.snapshot(), before)
        self.client_class.assert_not_called()

    def test_only_onboarding_staff_see_or_use_the_controls(self):
        invitation = self.invite(email=self.person["email"])
        member = UserFactory()
        member.groups.add(self.company.group)
        company_leader = UserFactory(is_staff=True)
        self.company.leaders.add(company_leader)
        nonstaff_root_leader = UserFactory()
        self.root.leaders.add(nonstaff_root_leader)
        # Signing each user in updates last_login, so compare invitations and mail only.
        before = (list(EnterpriseInvitation.objects.values()), Email.objects.count())
        for user in (member, company_leader, nonstaff_root_leader):
            with self.subTest(user=user.username):
                self.http.force_login(user)
                page = pq(self.http.get(self.page_url).content)
                self.assertFalse(page("#enterprise-invitations, #enterprise-invite-form"))
                self.assertEqual(self.http.post(self.invite_url, self.person).status_code, 403)
                self.assertEqual(self.http.post(self.resend_url(invitation)).status_code, 403)
        self.http.logout()
        self.assertEqual(self.http.post(self.resend_url(invitation)).status_code, 302)
        csrf_client = Client(enforce_csrf_checks=True)
        csrf_client.force_login(self.actor)
        self.assertEqual(csrf_client.post(self.resend_url(invitation)).status_code, 403)
        self.assertEqual(
            (list(EnterpriseInvitation.objects.values()), Email.objects.count()), before
        )
        self.client_class.assert_not_called()

    def test_other_companies_and_departments_cannot_be_targeted(self):
        elsewhere = self.invite(email="elsewhere@example.com", company=self.other_company)
        department = self.child(self.company)
        before = self.snapshot()
        self.assertEqual(self.http.post(self.resend_url(elsewhere)).status_code, 404)
        department_url = reverse("groups.invite_user", args=[department.slug])
        self.assertEqual(self.http.post(department_url, self.person).status_code, 404)
        self.assertEqual(self.snapshot(), before)
        self.client_class.assert_not_called()
