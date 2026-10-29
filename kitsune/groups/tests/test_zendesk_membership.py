import traceback
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from unittest.mock import call, patch

import requests
from celery.exceptions import Retry
from django.contrib.auth.models import User
from django.db import connections, transaction
from django.test import TransactionTestCase, override_settings
from zenpy.lib.api_objects import OrganizationMembership
from zenpy.lib.exception import APIException, ZenpyException

from kitsune.customercare.models import ZendeskOrganization
from kitsune.customercare.zendesk import ZendeskProvisioningConflict
from kitsune.groups.membership import lock_enterprise_hierarchy
from kitsune.groups.models import GroupProfile
from kitsune.groups.tasks import (
    ZendeskMembershipChanged,
    ZendeskUnavailable,
    remove_stale_zendesk_memberships,
    sync_enterprise_zendesk_membership,
)
from kitsune.groups.tests import (
    DepartmentFactory,
    EnterpriseCompanyFactory,
    EnterpriseInvitationFactory,
    GroupProfileFactory,
)
from kitsune.sumo.tests import TestCase
from kitsune.sumo.urlresolvers import reverse
from kitsune.users.identity import lock_account_email
from kitsune.users.models import Profile
from kitsune.users.tests import UserFactory


@override_settings(ENTERPRISE_GROUP_SLUG="membership-sync-root", READ_ONLY=False)
class EnterpriseZendeskMembershipTests(TestCase):
    def setUp(self):
        super().setUp()
        self.enqueue = self.enterContext(
            patch("kitsune.groups.tasks.sync_enterprise_zendesk_membership.delay")
        )
        self.cleanup = self.enterContext(
            patch("kitsune.groups.tasks.remove_stale_zendesk_memberships.delay")
        )
        self.client_class = self.enterContext(
            patch("kitsune.groups.tasks.ZendeskClient", autospec=True)
        )
        self.zendesk = self.client_class.return_value
        self.zendesk.ensure_organization.return_value = "101"
        self.zendesk.ensure_user.return_value = "201"
        self.zendesk.validate_removal_user.return_value = "201"
        self.zendesk.get_organization_memberships.return_value = []
        self.root = GroupProfileFactory(slug="membership-sync-root")
        self.company = EnterpriseCompanyFactory(root=self.root)
        self.department = DepartmentFactory(company=self.company)
        self.user = UserFactory(profile__fxa_uid="member-identity")

    def sync(self):
        sync_enterprise_zendesk_membership(self.user.pk)

    def test_company_add_enqueues_after_commit_once_and_provisions_all_remote_legs(self):
        with self.captureOnCommitCallbacks(execute=True):
            with transaction.atomic():
                self.user.groups.add(self.company.group, self.department.group)
                self.enqueue.assert_not_called()
        self.enqueue.assert_called_once_with(self.user.pk)

        self.sync()

        mapping = ZendeskOrganization.objects.get(group_profile=self.company)
        self.user.profile.refresh_from_db()
        self.assertEqual(mapping.zendesk_id, "101")
        self.assertEqual(self.user.profile.zendesk_id, "201")
        self.assertEqual(
            self.zendesk.ensure_organization.call_args.kwargs["external_id"],
            str(mapping.external_id),
        )
        self.assertEqual(self.zendesk.ensure_user.call_args.kwargs["email"], self.user.email)
        self.assertLess(
            self.zendesk.method_calls.index(
                call.remove_organization_memberships(
                    user_id="201", organization_ids=set(), memberships=[]
                )
            ),
            self.zendesk.method_calls.index(
                call.ensure_organization_membership(
                    user_id="201", organization_id="101", memberships=[]
                )
            ),
        )

    def test_moderator_member_and_leader_actions_enqueue(self):
        operator = UserFactory()
        self.root.leaders.add(operator)
        self.client.force_login(operator)
        for action in ("add_member", "add_leader"):
            with self.subTest(action=action):
                member = UserFactory()
                self.enqueue.reset_mock()
                with self.captureOnCommitCallbacks(execute=True):
                    response = self.client.post(
                        reverse(f"groups.{action}", args=[self.company.slug]),
                        {"users": member.username},
                    )
                self.assertRedirects(
                    response, self.company.get_absolute_url(), fetch_redirect_response=False
                )
                self.enqueue.assert_called_once_with(member.pk)

    def test_repeated_sync_reuses_saved_links_without_local_writes(self):
        self.user.groups.add(self.company.group)
        ZendeskOrganization.objects.create(group_profile=self.company, zendesk_id="00101")
        other = EnterpriseCompanyFactory(root=self.root)
        ZendeskOrganization.objects.create(group_profile=other, zendesk_id="102")
        ZendeskOrganization.objects.create(group_profile=self.department, zendesk_id="103")
        ZendeskOrganization.objects.create(group_profile=GroupProfileFactory())
        ZendeskOrganization.objects.create(group_profile=GroupProfileFactory(), zendesk_id="")
        memberships = [
            OrganizationMembership(organization_id=organization_id)
            for organization_id in (101, 102, 103, 999)
        ]
        self.zendesk.get_organization_memberships.return_value = memberships
        self.sync()
        self.zendesk.remove_organization_memberships.assert_called_once_with(
            user_id="201", organization_ids={"102", "103"}, memberships=memberships
        )
        self.zendesk.reset_mock()
        with (
            patch.object(ZendeskOrganization, "save") as save_mapping,
            patch.object(Profile, "save") as save_profile,
        ):
            self.sync()
        save_mapping.assert_not_called()
        save_profile.assert_not_called()
        self.assertEqual(self.zendesk.ensure_organization.call_args.kwargs["zendesk_id"], "101")
        self.assertEqual(self.zendesk.ensure_user.call_args.kwargs["zendesk_id"], "201")
        self.zendesk.get_organization_memberships.assert_called_once_with(user_id="201")
        self.zendesk.remove_organization_memberships.assert_called_once_with(
            user_id="201", organization_ids={"102", "103"}, memberships=memberships
        )
        self.zendesk.ensure_organization_membership.assert_called_once_with(
            user_id="201", organization_id="101", memberships=memberships
        )

    def test_department_member_syncs_the_company_and_leaving_cleans_linked_organizations(self):
        self.user.groups.add(self.department.group)
        self.sync()
        mapping = ZendeskOrganization.objects.get(group_profile=self.company)
        self.assertEqual(mapping.zendesk_id, "101")
        self.assertFalse(
            ZendeskOrganization.objects.filter(group_profile=self.department).exists()
        )
        self.assertEqual(
            self.zendesk.ensure_organization.call_args.kwargs["name"], self.company.group.name
        )
        other = EnterpriseCompanyFactory(root=self.root)
        ZendeskOrganization.objects.create(group_profile=other, zendesk_id="102")
        self.zendesk.reset_mock()
        with self.captureOnCommitCallbacks(execute=True):
            self.user.groups.remove(self.department.group)
        self.enqueue.assert_called_once_with(self.user.pk, removed_organization_ids=("101",))
        # The captured organization is still removed after its mapping is deleted.
        mapping.delete()
        sync_enterprise_zendesk_membership(
            *self.enqueue.call_args.args, **self.enqueue.call_args.kwargs
        )
        self.assertEqual(
            self.zendesk.method_calls,
            [
                call.validate_removal_user("201"),
                call.remove_organization_memberships(
                    user_id="201", organization_ids={"101", "102"}
                ),
            ],
        )

    def test_root_unrelated_and_empty_changes_do_not_enqueue(self):
        unrelated = GroupProfileFactory()
        for group in (self.root.group, unrelated.group):
            with self.captureOnCommitCallbacks(execute=True):
                self.user.groups.add(group)
                self.user.groups.remove(group)
                group.user_set.add(self.user)
                group.user_set.clear()
                self.user.groups.add(group)
                self.user.groups.clear()
        with self.captureOnCommitCallbacks(execute=True):
            self.company.group.user_set.add()
            self.company.group.user_set.clear()
        self.enqueue.assert_not_called()

    def test_forward_clear_captures_enterprise_membership_before_deletion(self):
        self.user.groups.add(self.company.group, self.department.group, self.root.group)
        with self.captureOnCommitCallbacks(execute=True):
            self.user.groups.clear()
            self.enqueue.assert_not_called()
        self.enqueue.assert_called_once_with(self.user.pk)

    def test_reverse_add_remove_and_clear_enqueue_each_affected_user_once(self):
        other = UserFactory()
        for action in ("add", "remove", "clear"):
            with self.subTest(action=action):
                if action == "clear":
                    self.company.group.user_set.add(self.user, other)
                self.enqueue.reset_mock()
                with self.captureOnCommitCallbacks(execute=True):
                    if action == "clear":
                        self.company.group.user_set.clear()
                    else:
                        getattr(self.company.group.user_set, action)(self.user, other, self.user)
                    self.enqueue.assert_not_called()
                self.assertCountEqual(
                    self.enqueue.call_args_list, [call(self.user.pk), call(other.pk)]
                )

    def test_publish_failure_does_not_raise_after_membership_is_saved(self):
        self.enqueue.side_effect = RuntimeError("Broker unavailable")
        with self.assertLogs(level="ERROR") as logs, self.captureOnCommitCallbacks(execute=True):
            self.user.groups.add(self.company.group)
        self.assertTrue(self.user.groups.filter(pk=self.company.group_id).exists())
        self.assertIn("Broker unavailable", logs.output[0])

    def test_ambiguous_legacy_membership_warns_without_any_provider_calls(self):
        other = EnterpriseCompanyFactory(root=self.root)
        User.groups.through.objects.bulk_create(
            [
                User.groups.through(user_id=self.user.pk, group_id=self.company.group_id),
                User.groups.through(user_id=self.user.pk, group_id=other.group_id),
            ]
        )
        for zendesk_id in ("", "201"):
            with self.subTest(zendesk_id=zendesk_id):
                Profile.all_profiles.filter(user=self.user).update(zendesk_id=zendesk_id)
                with (
                    patch.object(sync_enterprise_zendesk_membership, "retry") as retry,
                    self.assertLogs("k.task", level="WARNING") as logs,
                ):
                    self.sync()
                retry.assert_not_called()
                self.assertIn(f"user {self.user.pk}: company_conflict", logs.output[0])
        self.client_class.assert_not_called()
        self.assertFalse(ZendeskOrganization.objects.exists())

    def test_conflicts_log_a_safe_code_without_retrying_or_reaching_later_steps(self):
        def provider_conflict():
            self.user.groups.add(self.company.group)
            self.zendesk.ensure_organization.side_effect = ZendeskProvisioningConflict(
                "zendesk_conflict"
            )

        def organization_owned_by_another_company():
            self.user.groups.add(self.company.group)
            other = EnterpriseCompanyFactory(root=self.root)
            ZendeskOrganization.objects.create(group_profile=other, zendesk_id="101")

        def remote_user_owned_by_a_hidden_profile():
            self.user.groups.add(self.company.group)
            UserFactory(
                profile__zendesk_id="201", profile__account_type=Profile.AccountType.SYSTEM
            )

        def remote_user_claimed_during_setup():
            self.user.groups.add(self.company.group)
            self.zendesk.ensure_organization_membership.side_effect = lambda **kwargs: UserFactory(
                profile__zendesk_id="201"
            )

        def leaving_user_owned_by_another_profile():
            Profile.all_profiles.filter(user=self.user).update(zendesk_id="201")
            UserFactory(
                profile__zendesk_id="201", profile__account_type=Profile.AccountType.SYSTEM
            )

        def cleanup_of_an_ineligible_remote_user():
            self.zendesk.validate_removal_user.side_effect = ZendeskProvisioningConflict(
                "account_conflict"
            )

        def cleanup():
            remove_stale_zendesk_memberships(self.user.pk, "201", ("101",))

        for arrange, run, code, unreached, organization_id, profile_id in (
            (provider_conflict, self.sync, "zendesk_conflict", "ensure_user", None, ""),
            (
                organization_owned_by_another_company,
                self.sync,
                "zendesk_conflict",
                "ensure_user",
                None,
                "",
            ),
            (
                remote_user_owned_by_a_hidden_profile,
                self.sync,
                "account_conflict",
                "remove_organization_memberships",
                "101",
                "",
            ),
            (remote_user_claimed_during_setup, self.sync, "account_conflict", None, "101", ""),
            (
                leaving_user_owned_by_another_profile,
                self.sync,
                "account_conflict",
                "validate_removal_user",
                None,
                "201",
            ),
            (
                cleanup_of_an_ineligible_remote_user,
                cleanup,
                "account_conflict",
                "remove_organization_memberships",
                None,
                "",
            ),
        ):
            with self.subTest(arrange.__name__), transaction.atomic():
                self.zendesk.reset_mock(side_effect=True)
                arrange()
                with (
                    patch.object(sync_enterprise_zendesk_membership, "retry") as sync_retry,
                    patch.object(remove_stale_zendesk_memberships, "retry") as cleanup_retry,
                    self.assertLogs("k.task", level="WARNING") as logs,
                ):
                    run()
                self.assertIn(f"user {self.user.pk}: {code}", logs.output[0])
                sync_retry.assert_not_called()
                cleanup_retry.assert_not_called()
                if unreached:
                    getattr(self.zendesk, unreached).assert_not_called()
                self.assertEqual(
                    ZendeskOrganization.objects.filter(group_profile=self.company)
                    .values_list("zendesk_id", flat=True)
                    .first(),
                    organization_id,
                )
                self.assertEqual(Profile.all_profiles.get(user=self.user).zendesk_id, profile_id)
                transaction.set_rollback(True)

    def test_join_removes_captured_company_membership_but_not_target_or_external(self):
        self.user.groups.add(self.company.group)
        memberships = [
            OrganizationMembership(organization_id=organization_id)
            for organization_id in (101, 102, 999)
        ]
        self.zendesk.get_organization_memberships.return_value = memberships

        sync_enterprise_zendesk_membership(self.user.pk, removed_organization_ids=("101", "102"))

        self.assertEqual(
            self.zendesk.method_calls[-2:],
            [
                call.remove_organization_memberships(
                    user_id="201", organization_ids={"102"}, memberships=memberships
                ),
                call.ensure_organization_membership(
                    user_id="201", organization_id="101", memberships=memberships
                ),
            ],
        )

    def test_unclaimed_invitee_sync_does_not_bind_or_update_identity(self):
        Profile.all_profiles.filter(user=self.user).update(fxa_uid="")
        EnterpriseInvitationFactory(company=self.company, user=self.user, created_user=True)
        self.user.groups.add(self.company.group)
        self.sync()
        self.assertIsNone(self.zendesk.ensure_user.call_args.kwargs["fxa_uid"])
        self.zendesk.bind_user_identity.assert_not_called()
        self.zendesk.update_user.assert_not_called()
        profile = Profile.all_profiles.get(user=self.user)
        self.assertEqual(profile.fxa_uid, "")
        self.assertTrue(profile.is_unclaimed_invitee)
        self.assertEqual(profile.zendesk_id, "201")

    def test_email_change_before_lock_retries_without_provider_calls(self):
        @contextmanager
        def changed_email_lock(email):
            User.all_users.filter(pk=self.user.pk).update(email="changed@example.com")
            with lock_account_email(email):
                yield

        self.user.groups.add(self.company.group)
        with (
            patch("kitsune.groups.tasks.lock_account_email", changed_email_lock),
            patch.object(
                sync_enterprise_zendesk_membership, "retry", side_effect=Retry()
            ) as retry,
            self.assertRaises(Retry),
        ):
            self.sync()
        self.assertIsInstance(retry.call_args.kwargs["exc"], ZendeskMembershipChanged)
        self.client_class.assert_not_called()

    def test_provider_failures_retry_without_their_message_and_unexpected_errors_propagate(self):
        def response(status):
            response = requests.Response()
            response.status_code = status
            return response

        self.user.groups.add(self.company.group)
        url = (
            "https://support.zendesk.com/api/v2/users/search.json"
            f"?query=email:%22{self.user.email}%22"
        )
        for task, method, args in (
            (
                sync_enterprise_zendesk_membership,
                "remove_organization_memberships",
                (self.user.pk,),
            ),
            (
                remove_stale_zendesk_memberships,
                "validate_removal_user",
                (self.user.pk, "201", ("102",)),
            ),
        ):
            for error, status in (
                (
                    requests.HTTPError(
                        f"503 Server Error: Service Unavailable for url: {url}",
                        response=response(503),
                    ),
                    503,
                ),
                (requests.ConnectionError(f"Max retries exceeded with url: {url}"), None),
                (APIException(url, response=response(401)), 401),
                (ZenpyException(url), None),
            ):
                name = type(error).__name__
                with self.subTest(task=task.name, error=name):
                    getattr(self.zendesk, method).side_effect = error
                    with (
                        patch.object(task, "retry", side_effect=Retry()) as retry,
                        self.assertLogs("k.task", level="WARNING") as logs,
                        self.assertRaises(Retry),
                    ):
                        task(*args)
                    retried = retry.call_args.kwargs["exc"]
                    self.assertIsInstance(retried, ZendeskUnavailable)
                    self.assertEqual(retried.args, (name, status))
                    self.assertEqual(retry.call_args.kwargs["max_retries"], 6)
                    self.assertEqual(
                        logs.output,
                        [
                            "WARNING:k.task:Zendesk unavailable for user "
                            f"{self.user.pk}: {name} {status}"
                        ],
                    )
                    # Celery logs the retry reason; Sentry records the exception chain.
                    logged = repr(retried) + "".join(traceback.format_exception(retried))
                    self.assertNotIn(self.user.email, logged)
                    self.assertNotIn("zendesk.com", logged)
            with self.subTest(task=task.name, error="RuntimeError"):
                getattr(self.zendesk, method).side_effect = RuntimeError("worker failure")
                with (
                    patch.object(task, "retry") as retry,
                    self.assertRaisesRegex(RuntimeError, "worker failure"),
                ):
                    task(*args)
                retry.assert_not_called()
            getattr(self.zendesk, method).side_effect = None
        self.assertEqual(
            ZendeskOrganization.objects.get(group_profile=self.company).zendesk_id, "101"
        )
        self.assertEqual(Profile.all_profiles.get(user=self.user).zendesk_id, "201")

    def test_setup_invalidation_keeps_valid_links_and_queues_cleanup_for_the_resolved_pair(self):
        def replace_profile():
            Profile.all_profiles.filter(user=self.user).delete()
            Profile.all_profiles.create(user=self.user)

        for change, apply_change, organization_id, user_id, cleanup_queued in (
            (
                "email",
                lambda: User.all_users.filter(pk=self.user.pk).update(email="changed@example.com"),
                "101",
                "",
                True,
            ),
            (
                "fxa_uid",
                lambda: Profile.all_profiles.filter(user=self.user).update(fxa_uid="replacement"),
                "101",
                "",
                True,
            ),
            ("profile replacement", replace_profile, "101", "", True),
            (
                "profile relinked",
                lambda: Profile.all_profiles.filter(user=self.user).update(zendesk_id="202"),
                "101",
                "202",
                True,
            ),
            ("company deleted", self.company.delete, None, "201", True),
            (
                "organization relinked",
                lambda: ZendeskOrganization.objects.filter(group_profile=self.company).update(
                    zendesk_id="102"
                ),
                "102",
                "201",
                True,
            ),
            (
                "departure",
                lambda: self.user.groups.remove(self.company.group),
                "101",
                "201",
                False,
            ),
        ):
            with self.subTest(change=change), transaction.atomic():
                self.user.groups.add(self.company.group)
                self.zendesk.ensure_organization_membership.side_effect = lambda **kwargs: (
                    apply_change()
                )
                self.cleanup.reset_mock()
                with (
                    patch.object(
                        sync_enterprise_zendesk_membership, "retry", side_effect=Retry()
                    ) as retry,
                    self.captureOnCommitCallbacks(execute=True),
                    self.assertRaises(Retry),
                ):
                    self.sync()
                self.assertIsInstance(retry.call_args.kwargs["exc"], ZendeskMembershipChanged)
                self.assertEqual(
                    ZendeskOrganization.objects.filter(group_profile=self.company)
                    .values_list("zendesk_id", flat=True)
                    .first(),
                    organization_id,
                )
                self.assertEqual(Profile.all_profiles.get(user=self.user).zendesk_id, user_id)
                self.assertEqual(
                    self.cleanup.call_args_list,
                    [call(self.user.pk, "201", ("101",))] if cleanup_queued else [],
                )
                transaction.set_rollback(True)

    def test_saved_links_cleared_during_setup_are_not_restored(self):
        self.user.groups.add(self.company.group)
        mapping = ZendeskOrganization.objects.create(group_profile=self.company, zendesk_id="101")
        profile = Profile.all_profiles.filter(user=self.user)
        organization = ZendeskOrganization.objects.filter(pk=mapping.pk)

        for cleared_link, queryset, cleared_id in (
            ("organization", organization, None),
            ("organization", organization, ""),
            ("user", profile, ""),
        ):
            with self.subTest(cleared_link=cleared_link, cleared_id=cleared_id):
                organization.update(zendesk_id="101")
                profile.update(zendesk_id="201")
                self.zendesk.ensure_organization_membership.side_effect = lambda **kwargs: (
                    queryset.update(zendesk_id=cleared_id)
                )
                self.cleanup.reset_mock()

                with (
                    patch.object(
                        sync_enterprise_zendesk_membership, "retry", side_effect=Retry()
                    ) as retry,
                    self.captureOnCommitCallbacks(execute=True),
                    self.assertRaises(Retry),
                ):
                    self.sync()

                self.assertIsInstance(retry.call_args.kwargs["exc"], ZendeskMembershipChanged)
                mapping.refresh_from_db()
                self.assertEqual(
                    mapping.zendesk_id, cleared_id if cleared_link == "organization" else "101"
                )
                self.assertEqual(
                    profile.get().zendesk_id, cleared_id if cleared_link == "user" else "201"
                )
                self.cleanup.assert_called_once_with(self.user.pk, "201", ("101",))

    def test_cleanup_preserves_the_current_company_only_while_the_profile_owns_the_identity(self):
        self.user.groups.add(self.company.group)
        ZendeskOrganization.objects.create(group_profile=self.company, zendesk_id="00102")
        validate = call.validate_removal_user("201")
        for owned_id, captured, expected_calls in (
            (
                "201",
                ("101", "102"),
                [
                    validate,
                    call.remove_organization_memberships(user_id="201", organization_ids={"101"}),
                ],
            ),
            (
                "202",
                ("101", "102"),
                [
                    validate,
                    call.remove_organization_memberships(
                        user_id="201", organization_ids={"101", "102"}
                    ),
                ],
            ),
            ("201", ("102",), []),
        ):
            with self.subTest(owned_id=owned_id, captured=captured):
                Profile.all_profiles.filter(user=self.user).update(zendesk_id=owned_id)
                self.zendesk.reset_mock()
                remove_stale_zendesk_memberships(self.user.pk, "201", captured)
                self.assertEqual(self.zendesk.method_calls, expected_calls)

    def test_unlinked_missing_profile_deleted_user_and_read_only_skip_provider_calls(self):
        self.sync()
        self.assertEqual(self.zendesk.mock_calls, [])
        self.user.groups.add(self.company.group)
        with override_settings(READ_ONLY=True):
            self.sync()
        user_id = self.user.pk
        self.user.profile.delete()
        self.assertEqual(sync_enterprise_zendesk_membership(user_id), "profile_missing")
        User.all_users.filter(pk=user_id).delete()
        self.assertEqual(sync_enterprise_zendesk_membership(user_id), "user_missing")
        self.assertEqual(self.zendesk.mock_calls, [])


@override_settings(
    ENTERPRISE_GROUP_SLUG="membership-lock-root", READ_ONLY=False, ES_LIVE_INDEXING=False
)
class EnterpriseZendeskMembershipLockTests(TransactionTestCase):
    def test_remote_calls_only_hold_email_gate_and_mapping_uuid_is_already_committed(self):
        self.enterContext(patch("kitsune.groups.tasks.sync_enterprise_zendesk_membership.delay"))
        company = EnterpriseCompanyFactory()
        user = UserFactory()
        user.groups.add(company.group)

        def lock_resources(external_id):
            try:
                with connections["default"].cursor() as cursor:
                    cursor.execute("SET lock_timeout = '2s'")
                with lock_enterprise_hierarchy(exclusive=True):
                    GroupProfile.objects.select_for_update(nowait=True).get(pk=company.pk)
                    mapping = ZendeskOrganization.objects.select_for_update(nowait=True).get(
                        group_profile=company
                    )
                    self.assertEqual(str(mapping.external_id), external_id)
                    User.all_users.select_for_update(nowait=True).get(pk=user.pk)
                    Profile.all_profiles.select_for_update(nowait=True).get(user=user)
            finally:
                connections.close_all()

        def ensure_organization(**kwargs):
            with ThreadPoolExecutor(max_workers=1) as pool:
                pool.submit(lock_resources, kwargs["external_id"]).result(timeout=5)
            return "101"

        with patch("kitsune.groups.tasks.ZendeskClient", autospec=True) as client_class:
            client = client_class.return_value
            client.ensure_organization.side_effect = ensure_organization
            client.ensure_user.return_value = "201"
            sync_enterprise_zendesk_membership(user.pk)
        self.assertEqual(ZendeskOrganization.objects.get(group_profile=company).zendesk_id, "101")
        self.assertEqual(Profile.all_profiles.get(user=user).zendesk_id, "201")

    def test_deletion_during_first_provisioning_queues_only_completed_pair_after_commit(self):
        self.enterContext(patch("kitsune.groups.tasks.sync_enterprise_zendesk_membership.delay"))
        company = EnterpriseCompanyFactory()
        ZendeskOrganization.objects.create(
            group_profile=EnterpriseCompanyFactory(), zendesk_id="102"
        )
        user = UserFactory()
        user.groups.add(company.group)

        def delete_user():
            try:
                self.assertEqual(Profile.all_profiles.get(user=user).zendesk_id, "")
                User.all_users.get(pk=user.pk).delete()
                cleanup.assert_not_called()
            finally:
                connections.close_all()

        def ensure_membership(**kwargs):
            with ThreadPoolExecutor(max_workers=1) as pool:
                pool.submit(delete_user).result(timeout=5)

        def assert_committed(*args):
            self.assertFalse(connections["default"].in_atomic_block)

        with (
            patch("kitsune.groups.tasks.ZendeskClient", autospec=True) as client_class,
            patch("kitsune.groups.tasks.remove_stale_zendesk_memberships.delay") as cleanup,
            patch.object(
                sync_enterprise_zendesk_membership, "retry", side_effect=Retry()
            ) as retry,
        ):
            client = client_class.return_value
            client.ensure_organization.return_value = "101"
            client.ensure_user.return_value = "201"
            client.get_organization_memberships.return_value = []
            client.validate_removal_user.return_value = "201"
            client.ensure_organization_membership.side_effect = ensure_membership
            cleanup.side_effect = assert_committed

            with self.assertRaises(Retry):
                sync_enterprise_zendesk_membership(user.pk)

            self.assertIsInstance(retry.call_args.kwargs["exc"], ZendeskMembershipChanged)
            cleanup.assert_called_once_with(user.pk, "201", ("101",))
            self.assertFalse(User.all_users.filter(pk=user.pk).exists())
            client_class.reset_mock()
            client.reset_mock()

            sync_enterprise_zendesk_membership(user.pk)

            client_class.assert_not_called()
            remove_stale_zendesk_memberships(*cleanup.call_args.args)

            client.validate_removal_user.assert_called_once_with("201")
            client.remove_organization_memberships.assert_called_once_with(
                user_id="201", organization_ids={"101"}
            )
            client.ensure_organization_membership.assert_not_called()
