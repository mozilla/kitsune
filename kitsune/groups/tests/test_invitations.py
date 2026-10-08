from concurrent.futures import ThreadPoolExecutor
from queue import Queue
from threading import Event
from time import monotonic
from unittest.mock import patch

import psycopg
from django.conf import settings
from django.contrib.auth.models import AnonymousUser, User
from django.contrib.messages.storage.fallback import FallbackStorage
from django.core import mail
from django.core.exceptions import PermissionDenied, SuspiciousOperation, ValidationError
from django.db import IntegrityError, connections, transaction
from django.http import Http404
from django.test import RequestFactory, TransactionTestCase, override_settings
from django.utils import timezone
from post_office.models import Email
from waffle.testutils import override_switch

from kitsune.customercare.models import SupportTicket, ZendeskOrganization
from kitsune.customercare.tests import SupportTicketFactory
from kitsune.groups.models import EnterpriseInvitation, GroupProfile
from kitsune.groups.onboarding import invite_enterprise_user
from kitsune.groups.tests import EnterpriseInvitationFactory, GroupProfileFactory
from kitsune.products.models import Product, ProductSupportConfig, SupportOrganization
from kitsune.products.tests import (
    ProductFactory,
    ProductSupportConfigFactory,
    SupportOrganizationFactory,
    ZendeskConfigFactory,
)
from kitsune.questions.tests import AAQConfigFactory
from kitsune.sumo.tests import TestCase
from kitsune.users.auth import FXAAuthBackend
from kitsune.users.models import Profile
from kitsune.users.tests import GroupFactory, UserFactory


class InvitationFixtures:
    def setUp(self):
        super().setUp()
        self.enterContext(
            patch(
                "requests.sessions.Session.request",
                side_effect=AssertionError("Account preparation must not contact providers"),
            )
        )
        self.enterContext(patch("kitsune.customercare.signals.update_zendesk_user.delay"))
        self.enterContext(patch("kitsune.users.auth.update_zendesk_identity.delay"))
        self.root = GroupProfileFactory(
            slug=settings.ENTERPRISE_GROUP_SLUG,
            visibility=GroupProfile.Visibility.PRIVATE,
            isolation_enabled=True,
        )
        self.actor = UserFactory(is_staff=True)
        self.root.leaders.add(self.actor)
        self.product = ProductFactory(slug=self.root.slug)
        self.config = ProductSupportConfigFactory(
            product=self.product, zendesk_config=ZendeskConfigFactory()
        )
        self.company = self.child(self.root)
        self.other_company = self.child(self.root)

    def child(self, parent):
        return GroupProfile.objects.add_child(parent, create_kwargs={"group": GroupFactory()})

    def invite(self, **kwargs):
        return invite_enterprise_user(
            **{
                "actor": self.actor,
                "company": self.company,
                "email": "invited@example.com",
                "first_name": "Jamie",
                "last_name": "Rivera",
                **kwargs,
            }
        )

    def eligible_user(self, **kwargs):
        return UserFactory(
            **{
                "email": "invited@example.com",
                "first_name": "Existing",
                "last_name": "Person",
                "profile__fxa_uid": "existing-fxa-identity",
                **kwargs,
            }
        )

    def snapshot(self):
        querysets = (
            User.all_users,
            Profile.all_profiles,
            EnterpriseInvitation.objects,
            ZendeskOrganization.objects,
            SupportOrganization.objects,
            User.groups.through.objects,
            GroupProfile.leaders.through.objects,
            Email.objects,
            SupportTicket.objects,
        )
        return [list(queryset.order_by("pk").values()) for queryset in querysets]

    def assert_rejected(self, exception=ValidationError, code=None, **kwargs):
        before = self.snapshot()
        with self.assertRaises(exception) as raised:
            self.invite(**kwargs)
        self.assertEqual(self.snapshot(), before)
        if code:
            self.assertEqual(raised.exception.code, code)
        return raised.exception


@override_settings(
    TESTING=True,
    ENTERPRISE_GROUP_SLUG="invitation-enterprise-root",
    ENTERPRISE_ONBOARDING_LANDING_PATH="",
    ENTERPRISE_INVITATION_MAX_AGE=604800,
    READ_ONLY=False,
)
class EnterpriseInvitationTests(InvitationFixtures, TestCase):
    def test_new_account_is_private_and_unclaimed_without_granting_support(self):
        queued_before = Email.objects.count()
        sent_before = len(mail.outbox)
        with self.captureOnCommitCallbacks(execute=True):
            invitation = self.invite(
                email="  INVITED@Example.COM  ",
                first_name="  JaMíe  Ann  ",
                last_name="  Rivera  ",
            )
        user = User.all_users.get(pk=invitation.user_id)
        profile = Profile.all_profiles.get(user=user)
        self.assertEqual(invitation.email, "invited@example.com")
        self.assertEqual(user.email, invitation.email)
        self.assertEqual((user.first_name, user.last_name), ("JaMíe  Ann", "Rivera"))
        self.assertFalse(user.is_active)
        self.assertFalse(user.has_usable_password())
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertIsNone(user.last_login)
        self.assertEqual(profile.account_type, Profile.AccountType.REGULAR)
        self.assertFalse(profile.public_email)
        self.assertEqual(profile.name, "")
        self.assertFalse(profile.is_fxa_migrated)
        self.assertIsNone(profile.fxa_uid)
        self.assertEqual(profile.locale, settings.LANGUAGE_CODE)
        self.assertEqual(profile.zendesk_id, "")
        self.assertFalse(profile.products.exists())
        self.assertFalse(User.groups.through.objects.filter(user=user).exists())
        self.assertFalse(GroupProfile.objects.filter(leaders=user).exists())
        self.assertTrue(invitation.created_user)
        self.assertEqual(invitation.created_by_id, self.actor.pk)
        self.assertEqual(invitation.support_config_id, self.config.pk)
        self.assertEqual(invitation.status, EnterpriseInvitation.Status.PENDING)
        self.assertEqual(invitation.completed_actions, ["sumo_account"])
        self.assertIsNone(invitation.welcome_email_id)
        self.assertIsNone(invitation.email_queued_at)
        self.assertIsNone(invitation.accepted_at)
        self.assertEqual(Email.objects.count(), queued_before)
        self.assertEqual(len(mail.outbox), sent_before)
        mapping = ZendeskOrganization.objects.get(group_profile=self.company)
        self.assertIsNone(mapping.zendesk_id)
        self.assertTrue(
            SupportOrganization.objects.filter(
                group=self.company.group, config=self.config
            ).exists()
        )

    def test_each_required_field_and_length_is_validated_before_any_writes(self):
        invalid = (
            ("email", ""),
            ("email", " \t "),
            ("email", "not-an-address"),
            ("email", "Jamie <invited@example.com>"),
            ("email", "one@example.com,two@example.com"),
            ("email", f"{'a' * 64}@{'b' * 63}.{'c' * 63}.{'d' * 60}.com"),
            ("first_name", ""),
            ("first_name", " \t\n "),
            ("last_name", ""),
            ("last_name", " \t\n "),
            ("first_name", "x" * (User._meta.get_field("first_name").max_length + 1)),
            ("last_name", "x" * (User._meta.get_field("last_name").max_length + 1)),
        )
        for field, value in invalid:
            with self.subTest(field=field, value=value):
                error = self.assert_rejected(**{field: value})
                self.assertIn(field, error.error_dict)

    def test_email_normalization_does_not_merge_aliases(self):
        first = self.invite(email="  A.Person+support@GMAIL.COM  ")
        second = self.invite(email="aperson@gmail.com")
        self.assertEqual(first.email, "a.person+support@gmail.com")
        self.assertEqual(second.email, "aperson@gmail.com")
        self.assertNotEqual(first.user_id, second.user_id)

    def test_hidden_accounts_reserve_their_usernames(self):
        hidden = UserFactory(username="reserved", profile__account_type=Profile.AccountType.SYSTEM)
        invitation = self.invite(email="RESERVED@example.org")
        self.assertEqual(invitation.user.username, "reserved1")
        self.assertNotEqual(invitation.user_id, hidden.pk)
        hidden.refresh_from_db()
        self.assertEqual(hidden.username, "reserved")

    def test_empty_normalized_username_uses_unoccupied_fallback(self):
        UserFactory(username="enterprise-user", profile__account_type=Profile.AccountType.SYSTEM)
        invitation = self.invite(email="***@example.com")
        self.assertEqual(invitation.user.username, "enterprise-user1")
        self.assertEqual(invitation.user.email, "***@example.com")

    def test_existing_account_preserves_names_profile_identity_subscriptions_and_history(self):
        user = self.eligible_user(
            profile__name="Public pseudonym",
            profile__locale="de",
            profile__public_email=True,
            profile__zendesk_id="existing-zendesk-user",
            profile__fxa_refresh_token="existing-refresh-token",
        )
        subscription = ProductFactory()
        user.profile.products.add(subscription)
        unrelated = GroupProfileFactory()
        user.groups.add(unrelated.group)
        unrelated.leaders.add(user)
        ticket = SupportTicketFactory(user=user, product=self.product)
        before_user = User.all_users.filter(pk=user.pk).values().get()
        before_profile = Profile.all_profiles.filter(pk=user.pk).values().get()
        before_ticket = SupportTicket.objects.filter(pk=ticket.pk).values().get()
        invitation = self.invite(first_name="Replacement", last_name="Identity")
        self.assertEqual(invitation.user_id, user.pk)
        self.assertFalse(invitation.created_user)
        self.assertEqual(User.all_users.filter(pk=user.pk).values().get(), before_user)
        self.assertEqual(Profile.all_profiles.filter(pk=user.pk).values().get(), before_profile)
        self.assertEqual(SupportTicket.objects.filter(pk=ticket.pk).values().get(), before_ticket)
        self.assertQuerySetEqual(user.profile.products.all(), [subscription])
        self.assertEqual(
            set(User.groups.through.objects.filter(user=user).values_list("group_id", flat=True)),
            {unrelated.group_id},
        )
        self.assertQuerySetEqual(GroupProfile.objects.filter(leaders=user), [unrelated])

    def test_same_company_unfinished_invitation_preserves_names_and_progress(self):
        invitation = self.invite()
        for status in (
            EnterpriseInvitation.Status.PENDING,
            EnterpriseInvitation.Status.FAILED,
            EnterpriseInvitation.Status.READY,
        ):
            with self.subTest(status=status):
                EnterpriseInvitation.objects.filter(pk=invitation.pk).update(
                    status=status,
                    completed_actions=["sumo_account", "zendesk_organization"],
                    failed_action="zendesk_user",
                    error_code="zendesk_unavailable",
                    token_version=4,
                    email_queued_at=timezone.now(),
                )
                before = self.snapshot()
                repeated = self.invite(
                    email=" INVITED@EXAMPLE.COM ", first_name="Different", last_name="Names"
                )
                self.assertEqual(repeated.pk, invitation.pk)
                self.assertEqual(self.snapshot(), before)

    def test_unfinished_invitation_cannot_be_claimed_by_another_company(self):
        invitation = self.invite()
        self.assert_rejected(
            code="company_conflict", company=self.other_company, email=invitation.email.upper()
        )

    def test_accepted_current_member_returns_history_but_removed_member_can_be_reinvited(self):
        user = self.eligible_user()
        accepted = self.invite()
        accepted.status = EnterpriseInvitation.Status.ACCEPTED
        accepted.accepted_at = timezone.now()
        accepted.completed_actions = ["sumo_account", "sumo_membership", "welcome_email"]
        accepted.save()
        department = self.child(self.company)
        for membership in (self.company, department):
            with self.subTest(membership=membership.pk):
                user.groups.add(membership.group)
                before = self.snapshot()
                repeated = self.invite(first_name="Replacement", last_name="Names")
                self.assertEqual(repeated.pk, accepted.pk)
                self.assertEqual(self.snapshot(), before)
                user.groups.remove(membership.group)
        fresh = self.invite()
        self.assertNotEqual(fresh.pk, accepted.pk)
        self.assertEqual(fresh.user_id, user.pk)
        self.assertFalse(fresh.created_user)
        self.assertEqual(fresh.completed_actions, ["sumo_account"])
        accepted.refresh_from_db()
        self.assertEqual(accepted.status, EnterpriseInvitation.Status.ACCEPTED)
        self.assertEqual(EnterpriseInvitation.objects.filter(user=user).count(), 2)
        self.assertFalse(User.groups.through.objects.filter(user=user).exists())

    def test_ineligible_existing_accounts_are_not_activated_or_modified(self):
        cases = (
            {"is_active": False},
            {"is_staff": True},
            {"is_superuser": True},
            {"profile__account_type": Profile.AccountType.SYSTEM},
            {"profile__account_type": Profile.AccountType.ADMIN},
            {"profile": None},
            {"profile__fxa_uid": None, "profile__is_fxa_migrated": False},
            {"profile__fxa_uid": ""},
        )
        for index, kwargs in enumerate(cases):
            with self.subTest(account=kwargs):
                options = {
                    "email": f"ineligible-{index}@example.com",
                    "profile__fxa_uid": f"ineligible-fxa-{index}",
                    **kwargs,
                }
                if options.get("profile", True) is None:
                    options.pop("profile__fxa_uid")
                user = UserFactory(**options)
                self.assert_rejected(code="account_conflict", email=user.email.upper())

    def test_case_insensitive_duplicates_include_hidden_accounts(self):
        regular = self.eligible_user(email="duplicate@example.com")
        UserFactory(
            email="DUPLICATE@example.com", profile__account_type=Profile.AccountType.SYSTEM
        )
        self.assert_rejected(code="account_conflict", email=regular.email)

    def test_deleted_prepared_account_is_not_recreated(self):
        invitation = self.invite()
        invitation.user.delete()
        self.assert_rejected(code="resource_missing")
        invitation.refresh_from_db()
        self.assertIsNone(invitation.user_id)
        self.assertEqual(invitation.completed_actions, ["sumo_account"])

    def test_deleted_captured_config_is_not_replaced_with_current_config(self):
        invitation = self.invite()
        self.config.delete()
        self.config = ProductSupportConfigFactory(
            product=self.product, zendesk_config=ZendeskConfigFactory()
        )
        self.assert_rejected(code="configuration_error")
        invitation.refresh_from_db()
        self.assertIsNone(invitation.support_config_id)

    def test_deleted_support_or_mapping_is_not_recreated_for_existing_invitation(self):
        self.invite()
        SupportOrganization.objects.filter(group=self.company.group).delete()
        self.assert_rejected(code="configuration_error")
        SupportOrganizationFactory(group=self.company.group, config=self.config)
        ZendeskOrganization.objects.filter(group_profile=self.company).delete()
        self.assert_rejected(code="configuration_error")

    def test_other_company_or_its_department_membership_prevents_intake(self):
        user = self.eligible_user()
        department = self.child(self.other_company)
        for membership in (self.other_company, department):
            with self.subTest(membership=membership.pk):
                user.groups.add(membership.group)
                self.assert_rejected(code="company_conflict")
                user.groups.remove(membership.group)

    def test_other_organization_for_captured_config_conflicts_even_outside_enterprise_tree(self):
        user = self.eligible_user()
        unrelated = GroupProfileFactory()
        SupportOrganizationFactory(group=unrelated.group, config=self.config)
        department = self.child(unrelated)
        user.groups.add(department.group)
        self.assert_rejected(code="company_conflict")

    def test_other_product_organization_is_preserved(self):
        user = self.eligible_user()
        unrelated = GroupProfileFactory()
        other_config = ProductSupportConfigFactory(zendesk_config=ZendeskConfigFactory())
        organization = SupportOrganizationFactory(group=unrelated.group, config=other_config)
        user.groups.add(unrelated.group)
        invitation = self.invite()
        self.assertEqual(invitation.user_id, user.pk)
        self.assertTrue(SupportOrganization.objects.filter(pk=organization.pk).exists())
        self.assertTrue(
            User.groups.through.objects.filter(user=user, group=unrelated.group).exists()
        )
        self.assertFalse(
            User.groups.through.objects.filter(user=user, group=self.company.group).exists()
        )

    def test_only_active_staff_root_moderators_can_invite(self):
        root_leader = UserFactory()
        inactive_leader = UserFactory(is_staff=True, is_active=False)
        company_leader = UserFactory(is_staff=True)
        root_member = UserFactory(is_staff=True)
        self.root.leaders.add(root_leader, inactive_leader)
        self.company.leaders.add(company_leader)
        root_member.groups.add(self.root.group)
        for actor in (
            None,
            AnonymousUser(),
            root_leader,
            inactive_leader,
            company_leader,
            root_member,
            UserFactory(is_staff=True),
            UserFactory(is_superuser=True, is_staff=False),
        ):
            with self.subTest(actor=actor):
                self.assert_rejected(PermissionDenied, actor=actor)

    def test_staff_superuser_can_prepare_without_becoming_member_or_leader(self):
        actor = UserFactory(is_staff=True, is_superuser=True)
        invitation = self.invite(actor=actor)
        self.assertEqual(invitation.created_by_id, actor.pk)
        self.assertFalse(User.groups.through.objects.filter(user=actor).exists())
        self.assertFalse(GroupProfile.objects.filter(leaders=actor).exists())

    @override_settings(READ_ONLY=True)
    def test_read_only_refuses_intake(self):
        self.assert_rejected(PermissionDenied)

    def test_only_saved_direct_companies_of_configured_root_are_eligible(self):
        department = self.child(self.company)
        other_root = GroupProfileFactory()
        other_company = self.child(other_root)
        other_company.path = self.company.path
        other_company.depth = self.company.depth
        for company in (self.root, department, other_root, other_company):
            with self.subTest(company=company.pk):
                self.assert_rejected(Http404, company=company)

    def test_missing_nested_or_unsafe_root_refuses_intake(self):
        for slug in ("missing-enterprise-root", self.company.slug):
            with self.subTest(slug=slug), override_settings(ENTERPRISE_GROUP_SLUG=slug):
                self.assert_rejected(code="configuration_error")
        for changes in (
            {"visibility": GroupProfile.Visibility.PUBLIC},
            {"visibility": GroupProfile.Visibility.PRIVATE, "isolation_enabled": False},
        ):
            with self.subTest(changes=changes):
                GroupProfile.objects.filter(pk=self.root.pk).update(**changes)
                self.assert_rejected(code="configuration_error")

    def test_unusable_product_and_support_prerequisites_refuse_intake(self):
        for changes in ({"slug": "unrelated-product"}, {"is_archived": True}):
            with self.subTest(product=changes):
                Product.objects.filter(pk=self.product.pk).update(**changes)
                self.assert_rejected(code="configuration_error")
                Product.objects.filter(pk=self.product.pk).update(
                    slug=self.root.slug, is_archived=False
                )
        duplicate = ProductFactory(slug=self.product.slug)
        self.assert_rejected(code="configuration_error")
        duplicate.delete()
        for changes in (
            {"is_active": False},
            {"subscription_only": True},
            {"zendesk_config": None, "forum_config": AAQConfigFactory()},
            {"unsubscribed_redirect_product": ProductFactory()},
        ):
            with self.subTest(config=changes):
                ProductSupportConfig.objects.filter(pk=self.config.pk).update(**changes)
                self.assert_rejected(code="configuration_error")
                self.config.save()
        self.config.delete()
        self.assert_rejected(code="configuration_error")

    def test_invalid_ticket_form_refuses_intake(self):
        zendesk = self.config.zendesk_config
        for ticket_form_id in ("", " ", "0", "-1", "1.5", "invalid", "１２"):
            with self.subTest(ticket_form_id=ticket_form_id):
                zendesk.ticket_form_id = ticket_form_id
                zendesk.save()
                self.assert_rejected(code="configuration_error")

    @override_settings(
        ZENDESK_CHAT_WIDGET_KEY="test-widget",
        ZENDESK_CHAT_SIGNING_KEY_ID="test-key",
        ZENDESK_CHAT_SIGNING_SECRET="test-secret",
    )
    def test_existing_chat_entitlement_requires_usable_chat_deployment(self):
        SupportOrganizationFactory(
            group=self.company.group, config=self.config, include_live_chat=True
        )
        with override_switch("zendesk-chat", active=False):
            self.assert_rejected(code="configuration_error")
        with override_switch("zendesk-chat", active=True):
            for setting in (
                "ZENDESK_CHAT_WIDGET_KEY",
                "ZENDESK_CHAT_SIGNING_KEY_ID",
                "ZENDESK_CHAT_SIGNING_SECRET",
            ):
                with self.subTest(setting=setting), override_settings(**{setting: ""}):
                    self.assert_rejected(code="configuration_error")
            invitation = self.invite()
        self.assertEqual(invitation.support_config_id, self.config.pk)
        self.assertTrue(
            SupportOrganization.objects.get(
                group=self.company.group, config=self.config
            ).include_live_chat
        )

    def test_invalid_landing_path_or_expiry_leaves_no_partial_account(self):
        for path in (
            "https://other.example/support",
            "//other.example/support",
            "relative/path",
            "/\\other.example/support",
            "/support\nheader",
            "/support\x7f",
        ):
            with (
                self.subTest(path=path),
                override_settings(ENTERPRISE_ONBOARDING_LANDING_PATH=path),
            ):
                self.assert_rejected(code="configuration_error")
        for expiry in (0, -1, "604800", None):
            with (
                self.subTest(expiry=expiry),
                override_settings(ENTERPRISE_INVITATION_MAX_AGE=expiry),
            ):
                self.assert_rejected(code="configuration_error")

    @override_settings(ENTERPRISE_ONBOARDING_LANDING_PATH="/enterprise/support?source=invitation")
    def test_local_landing_path_allows_intake(self):
        invitation = self.invite()
        self.assertEqual(invitation.completed_actions, ["sumo_account"])
        self.assertFalse(invitation.user.is_active)

    def test_database_allows_history_but_only_one_case_insensitive_open_invitation(self):
        user = self.eligible_user()
        first = EnterpriseInvitationFactory(
            company=self.company,
            support_config=self.config,
            user=user,
            email=user.email,
            status=EnterpriseInvitation.Status.ACCEPTED,
        )
        historical = EnterpriseInvitationFactory(
            company=self.other_company,
            support_config=self.config,
            user=user,
            email=user.email.upper(),
            status=EnterpriseInvitation.Status.ACCEPTED,
        )
        unfinished = EnterpriseInvitationFactory(
            company=self.company, support_config=self.config, user=user, email=user.email.upper()
        )
        for status in (
            EnterpriseInvitation.Status.PENDING,
            EnterpriseInvitation.Status.FAILED,
            EnterpriseInvitation.Status.READY,
        ):
            with self.subTest(status=status):
                with self.assertRaises(IntegrityError), transaction.atomic():
                    EnterpriseInvitationFactory(
                        company=self.other_company,
                        support_config=self.config,
                        user=user,
                        email=user.email,
                        status=status,
                    )
        self.assertEqual(
            set(EnterpriseInvitation.objects.values_list("pk", flat=True)),
            {first.pk, historical.pk, unfinished.pk},
        )


@override_settings(
    TESTING=True,
    ES_LIVE_INDEXING=False,
    ENTERPRISE_GROUP_SLUG="invitation-concurrency-root",
    ENTERPRISE_ONBOARDING_LANDING_PATH="",
    ENTERPRISE_INVITATION_MAX_AGE=604800,
    READ_ONLY=False,
    FXA_OP_TOKEN_ENDPOINT="https://server.example.com/token",
    FXA_OP_USER_ENDPOINT="https://server.example.com/user",
    FXA_RP_CLIENT_ID="example_id",
    FXA_RP_CLIENT_SECRET="client_secret",
    FXA_CREATE_USER=True,
    FXA_RP_SCOPES="openid email profile",
)
class EnterpriseInvitationConcurrencyTests(InvitationFixtures, TransactionTestCase):
    def backend(self):
        backend = FXAAuthBackend()
        backend.request = RequestFactory().get("/fxa/callback/")
        backend.request.session = {}
        backend.request._messages = FallbackStorage(backend.request)
        return backend

    def signup(self, claims):
        backend = self.backend()
        with patch.object(backend, "get_userinfo", return_value=claims):
            return backend.get_or_create_user("access", "id", {}).pk

    def compete(self, first, second):
        """Hold the first service's transaction until PostgreSQL proves the second waits."""
        prepared = Event()
        release = Event()
        first_pid = Queue()
        second_pid = Queue()

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
                            raise AssertionError(
                                "Competing operation never reached the email lock"
                            )
                return result
            except ValidationError as error:
                return error.code
            except SuspiciousOperation:
                return "invitation_required"
            finally:
                connection.close()

        observer_params = connections["default"].get_connection_params()
        observer_params["autocommit"] = True
        # The bounded Django pool must remain available to both racing workers.
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
                        self.fail(
                            f"Competing operation bypassed the email lock: {contender.result()!r}"
                        )
                    release.wait(0.01)
                else:
                    self.fail(f"Competing connection did not wait for the email lock: {state!r}")
            finally:
                release.set()
            return owner.result(timeout=15), contender.result(timeout=15)

    def assert_single_invitee(self, invitation):
        users = User.all_users.filter(email__iexact=invitation.email)
        self.assertEqual(list(users.values_list("pk", flat=True)), [invitation.user_id])
        self.assertEqual(Profile.all_profiles.filter(user__in=users).count(), 1)
        self.assertEqual(
            list(EnterpriseInvitation.objects.values_list("pk", flat=True)), [invitation.pk]
        )
        self.assertFalse(User.groups.through.objects.filter(user_id=invitation.user_id).exists())
        self.assertFalse(GroupProfile.objects.filter(leaders=invitation.user_id).exists())
        self.assertFalse(Email.objects.exists())

    def test_simultaneous_same_email_invites_reuse_one_prepared_account(self):
        first, second = self.compete(
            lambda: self.invite(first_name="First", last_name="Person").pk,
            lambda: self.invite(email=" INVITED@EXAMPLE.COM ", first_name="Second").pk,
        )
        self.assertEqual(first, second)
        invitation = EnterpriseInvitation.objects.get(pk=first)
        self.assert_single_invitee(invitation)
        self.assertEqual(invitation.user.first_name, "First")
        self.assertEqual(invitation.completed_actions, ["sumo_account"])

    def test_simultaneous_different_company_invites_have_one_owner(self):
        first, second = self.compete(
            lambda: self.invite().pk,
            lambda: self.invite(company=self.other_company, email="INVITED@example.com").pk,
        )
        self.assertEqual(second, "company_conflict")
        invitation = EnterpriseInvitation.objects.get(pk=first)
        self.assert_single_invitee(invitation)
        self.assertEqual(invitation.company_id, self.company.pk)
        self.assertFalse(
            ZendeskOrganization.objects.filter(group_profile=self.other_company).exists()
        )

    def test_intake_winning_signup_race_leaves_unclaimed_account_without_provider_mutation(self):
        claims = {
            "email": "INVITED@example.com",
            "uid": "authenticated-fxa-identity",
            "displayName": "Must not replace captured identity",
        }

        first, second = self.compete(lambda: self.invite().pk, lambda: self.signup(claims))
        self.assertEqual(second, "invitation_required")
        invitation = EnterpriseInvitation.objects.get(pk=first)
        self.assert_single_invitee(invitation)
        self.assertTrue(invitation.created_user)
        self.assertFalse(invitation.user.is_active)
        self.assertFalse(invitation.user.has_usable_password())
        self.assertIsNone(invitation.user.profile.fxa_uid)
        self.assertEqual(invitation.user.profile.name, "")
        self.assertEqual(invitation.user.first_name, "Jamie")

    def test_signup_winning_intake_race_is_reused_without_replacing_provider_identity(self):
        claims = {
            "email": "INVITED@example.com",
            "uid": "authenticated-fxa-identity",
            "displayName": "Authenticated public name",
            "subscriptions": [],
        }

        user_id, invitation_id = self.compete(
            lambda: self.signup(claims), lambda: self.invite().pk
        )
        invitation = EnterpriseInvitation.objects.get(pk=invitation_id)
        self.assert_single_invitee(invitation)
        self.assertEqual(invitation.user_id, user_id)
        self.assertFalse(invitation.created_user)
        self.assertTrue(invitation.user.is_active)
        self.assertEqual(invitation.user.profile.fxa_uid, claims["uid"])
        self.assertEqual(invitation.user.profile.name, claims["displayName"])
        self.assertEqual(invitation.user.first_name, "")

    def test_simultaneous_signups_reuse_one_account(self):
        claims = {
            "email": "INVITED@example.com",
            "uid": "authenticated-fxa-identity",
            "displayName": "First public name",
        }
        first, second = self.compete(
            lambda: self.signup(claims),
            lambda: self.signup({**claims, "displayName": "Second public name"}),
        )

        self.assertEqual(first, second)
        self.assertEqual(
            list(
                User.all_users.filter(email__iexact=claims["email"]).values_list("pk", flat=True)
            ),
            [first],
        )
        profile = Profile.all_profiles.get(user_id=first)
        self.assertEqual(profile.fxa_uid, claims["uid"])
        self.assertEqual(profile.name, claims["displayName"])
        self.assertTrue(profile.is_fxa_migrated)
        self.assertFalse(EnterpriseInvitation.objects.exists())

    def test_background_email_update_winning_race_is_reused_by_intake(self):
        user = self.eligible_user(email="original@example.com")

        def update():
            return (
                self.backend()
                .update_user(
                    User.all_users.get(pk=user.pk),
                    {"uid": user.profile.fxa_uid, "email": "INVITED@example.com"},
                )
                .pk
            )

        user_id, invitation_id = self.compete(update, lambda: self.invite().pk)
        invitation = EnterpriseInvitation.objects.get(pk=invitation_id)
        self.assert_single_invitee(invitation)
        self.assertEqual(invitation.user_id, user_id)
        self.assertEqual(user_id, user.pk)
        self.assertFalse(invitation.created_user)
        self.assertEqual(invitation.user.first_name, "Existing")

    def test_intake_winning_email_update_race_preserves_both_original_identities(self):
        user = self.eligible_user(
            email="original@example.com", profile__name="Original public name"
        )
        profile_before = Profile.all_profiles.filter(user=user).values().get()

        def update():
            return self.backend().update_user(
                User.all_users.get(pk=user.pk),
                {
                    "uid": user.profile.fxa_uid,
                    "email": "INVITED@example.com",
                    "displayName": "Should not be applied",
                },
            )

        invitation_id, result = self.compete(lambda: self.invite().pk, update)
        self.assertIsNone(result)
        invitation = EnterpriseInvitation.objects.get(pk=invitation_id)
        self.assert_single_invitee(invitation)
        self.assertNotEqual(invitation.user_id, user.pk)
        user.refresh_from_db()
        self.assertEqual(user.email, "original@example.com")
        self.assertEqual(Profile.all_profiles.filter(user=user).values().get(), profile_before)
        self.assertFalse(invitation.user.is_active)
        self.assertIsNone(invitation.user.profile.fxa_uid)
