from unittest.mock import call, patch

from django.contrib.auth.models import User
from django.db import transaction
from django.test import TransactionTestCase, override_settings

from kitsune.customercare.models import ZendeskOrganization
from kitsune.customercare.zendesk import ZendeskProvisioningConflict
from kitsune.groups.tasks import (
    remove_stale_zendesk_memberships,
    sync_enterprise_zendesk_membership,
)
from kitsune.groups.tests import DepartmentFactory, EnterpriseCompanyFactory, GroupProfileFactory
from kitsune.users.models import Profile
from kitsune.users.tests import UserFactory


@override_settings(
    ENTERPRISE_GROUP_SLUG="deleted-member-root", READ_ONLY=False, ES_LIVE_INDEXING=False
)
class DeletedUserZendeskMembershipTests(TransactionTestCase):
    def setUp(self):
        super().setUp()
        self.enterContext(patch("kitsune.customercare.tasks.update_zendesk_user.delay"))
        self.sync_enqueue = self.enterContext(
            patch("kitsune.groups.tasks.sync_enterprise_zendesk_membership.delay")
        )
        self.enqueue = self.enterContext(
            patch("kitsune.groups.tasks.remove_stale_zendesk_memberships.delay")
        )
        self.client_class = self.enterContext(
            patch("kitsune.groups.tasks.ZendeskClient", autospec=True)
        )
        self.zendesk = self.client_class.return_value
        self.zendesk.validate_removal_user.return_value = "201"
        self.root = GroupProfileFactory(slug="deleted-member-root")
        self.company = EnterpriseCompanyFactory(root=self.root)
        self.department = DepartmentFactory(company=self.company)
        self.mapping = ZendeskOrganization.objects.create(
            group_profile=self.company, zendesk_id="101"
        )
        self.user = UserFactory(profile__zendesk_id="201")

    def test_deletion_captures_all_linked_ids_and_publishes_only_after_commit(self):
        other_company = EnterpriseCompanyFactory(root=self.root)
        ZendeskOrganization.objects.create(group_profile=other_company, zendesk_id="102")
        unlinked_company = EnterpriseCompanyFactory(root=self.root)
        ZendeskOrganization.objects.create(group_profile=unlinked_company)
        ZendeskOrganization.objects.create(
            group_profile=EnterpriseCompanyFactory(root=self.root), zendesk_id=""
        )
        self.user.groups.add(self.company.group, self.department.group)
        user_id = self.user.pk

        with transaction.atomic():
            self.user.delete()
            self.assertFalse(User.all_users.filter(pk=user_id).exists())
            self.assertFalse(Profile.all_profiles.filter(user_id=user_id).exists())
            self.enqueue.assert_not_called()

        self.enqueue.assert_called_once_with(user_id, "201", ("101", "102"))
        self.client_class.assert_not_called()

    def test_department_only_member_deletion_queues_cleanup(self):
        self.user.groups.add(self.department.group)
        user_id = self.user.pk

        self.user.delete()

        self.enqueue.assert_called_once_with(user_id, "201", ("101",))
        self.client_class.assert_not_called()

    def test_last_membership_removed_then_user_deleted_before_sync_cleans_old_organization(self):
        self.user.groups.add(self.company.group)
        self.sync_enqueue.reset_mock()
        user_id = self.user.pk

        self.user.groups.remove(self.company.group)
        self.sync_enqueue.assert_called_once_with(user_id, removed_organization_ids=("101",))
        self.enqueue.reset_mock()
        self.user.delete()
        self.enqueue.assert_called_once_with(user_id, "201", ("101",))
        self.assertFalse(User.all_users.filter(pk=user_id).exists())
        self.assertFalse(Profile.all_profiles.filter(user_id=user_id).exists())

        sync_enterprise_zendesk_membership(*self.sync_enqueue.call_args.args)

        self.client_class.assert_not_called()

        remove_stale_zendesk_memberships(*self.enqueue.call_args.args)

        self.zendesk.validate_removal_user.assert_called_once_with("201")
        self.zendesk.remove_organization_memberships.assert_called_once_with(
            user_id="201", organization_ids={"101"}
        )
        self.zendesk.ensure_user.assert_not_called()
        self.zendesk.ensure_organization.assert_not_called()
        self.zendesk.ensure_organization_membership.assert_not_called()

    def test_company_deletion_before_workers_keeps_cleanup_identities(self):
        for delete_user in (False, True):
            with self.subTest(delete_user=delete_user):
                organization_id = "102" if delete_user else "103"
                remote_user_id = "202" if delete_user else "203"
                company = EnterpriseCompanyFactory(root=self.root)
                ZendeskOrganization.objects.create(
                    group_profile=company, zendesk_id=organization_id
                )
                user = UserFactory(profile__zendesk_id=remote_user_id)
                user.groups.add(company.group)
                user_id = user.pk
                self.enqueue.reset_mock()

                with transaction.atomic():
                    if not delete_user:
                        user.groups.remove(company.group)
                    company.delete()
                    if delete_user:
                        user.delete()
                    self.enqueue.assert_not_called()

                self.enqueue.assert_any_call(user_id, remote_user_id, (organization_id,))
                self.zendesk.reset_mock()
                self.zendesk.validate_removal_user.return_value = remote_user_id
                remove_stale_zendesk_memberships(user_id, remote_user_id, (organization_id,))
                self.zendesk.remove_organization_memberships.assert_called_once_with(
                    user_id=remote_user_id, organization_ids={organization_id}
                )

    def test_task_removes_only_captured_ids_after_user_profile_and_mapping_deletion(self):
        self.user.groups.add(self.company.group)
        user_id = self.user.pk
        with transaction.atomic():
            self.user.delete()
            self.mapping.delete()

        other_company = EnterpriseCompanyFactory(root=self.root)
        ZendeskOrganization.objects.create(group_profile=other_company, zendesk_id="102")
        self.enqueue.assert_called_once_with(user_id, "201", ("101",))
        self.assertFalse(User.all_users.filter(pk=user_id).exists())
        self.assertFalse(Profile.all_profiles.filter(user_id=user_id).exists())
        self.client_class.assert_not_called()

        remove_stale_zendesk_memberships(*self.enqueue.call_args.args)

        self.zendesk.validate_removal_user.assert_called_once_with("201")
        self.zendesk.remove_organization_memberships.assert_called_once_with(
            user_id="201", organization_ids={"101"}
        )
        self.zendesk.ensure_user.assert_not_called()
        self.zendesk.ensure_organization.assert_not_called()
        self.zendesk.ensure_organization_membership.assert_not_called()

    def test_nonmember_root_only_and_unrelated_users_queue_captured_cleanup(self):
        unrelated = GroupProfileFactory()
        expected_calls = []
        for group in (None, self.root.group, unrelated.group):
            with self.subTest(group=group):
                user = UserFactory(profile__zendesk_id="202")
                if group is not None:
                    user.groups.add(group)
                expected_calls.append(call(user.pk, "202", ("101",)))
                user.delete()

        self.assertEqual(self.enqueue.call_args_list, expected_calls)
        self.client_class.assert_not_called()

    def test_company_leadership_without_membership_queues_captured_cleanup(self):
        self.company.leaders.add(self.user)
        user_id = self.user.pk

        self.user.delete()

        self.enqueue.assert_called_once_with(user_id, "201", ("101",))
        self.client_class.assert_not_called()

    @override_settings(ENTERPRISE_GROUP_SLUG="missing-enterprise-root")
    def test_linked_user_without_enterprise_root_queues_captured_cleanup(self):
        user_id = self.user.pk

        self.user.delete()

        self.enqueue.assert_called_once_with(user_id, "201", ("101",))
        self.client_class.assert_not_called()

    def test_member_without_saved_remote_id_does_not_queue_cleanup(self):
        self.user.groups.add(self.company.group)
        Profile.all_profiles.filter(user=self.user).update(zendesk_id="")

        self.user.delete()

        self.enqueue.assert_not_called()
        self.client_class.assert_not_called()

    def test_member_without_profile_does_not_queue_cleanup(self):
        self.user.groups.add(self.company.group)
        self.user.profile.delete()

        self.user.delete()

        self.enqueue.assert_not_called()
        self.client_class.assert_not_called()

    def test_ambiguous_legacy_memberships_queue_captured_cleanup(self):
        self.user.groups.add(self.company.group)
        other_company = EnterpriseCompanyFactory(root=self.root)
        ZendeskOrganization.objects.create(group_profile=other_company, zendesk_id="102")
        User.groups.through.objects.create(user=self.user, group=other_company.group)
        user_id = self.user.pk

        self.user.delete()
        self.assertFalse(User.all_users.filter(pk=user_id).exists())
        self.enqueue.assert_called_once_with(user_id, "201", ("101", "102"))
        self.client_class.assert_not_called()

    def test_other_profile_owning_saved_id_logs_safe_code_without_cleanup(self):
        other = UserFactory(
            profile__zendesk_id="201", profile__account_type=Profile.AccountType.SYSTEM
        )
        user_id = self.user.pk

        with self.assertLogs("k.groups", level="WARNING") as logs:
            self.user.delete()

        self.assertEqual(
            logs.output,
            [
                "WARNING:k.groups:Zendesk deleted-user membership conflict "
                f"for user {user_id}: account_conflict"
            ],
        )
        self.assertTrue(Profile.all_profiles.filter(user=other, zendesk_id="201").exists())
        self.enqueue.assert_not_called()
        self.client_class.assert_not_called()

    def test_task_rejects_saved_id_claimed_after_deletion(self):
        self.user.groups.add(self.company.group)
        user_id = self.user.pk
        self.user.delete()
        UserFactory(profile__zendesk_id="201", profile__account_type=Profile.AccountType.SYSTEM)

        with self.assertLogs("k.task", level="WARNING") as logs:
            remove_stale_zendesk_memberships(*self.enqueue.call_args.args)

        self.assertIn(f"user {user_id}", logs.output[0])
        self.assertIn("account_conflict", logs.output[0])
        self.zendesk.remove_organization_memberships.assert_not_called()

    def test_task_rejects_elevated_or_shared_remote_identity(self):
        self.user.groups.add(self.company.group)
        self.user.delete()
        self.zendesk.validate_removal_user.side_effect = ZendeskProvisioningConflict(
            "account_conflict"
        )

        with self.assertLogs("k.task", level="WARNING") as logs:
            remove_stale_zendesk_memberships(*self.enqueue.call_args.args)

        self.assertIn("account_conflict", logs.output[0])
        self.zendesk.validate_removal_user.assert_called_once_with("201")
        self.zendesk.remove_organization_memberships.assert_not_called()

    def test_unexpected_provider_error_is_not_retried(self):
        self.user.delete()
        self.zendesk.validate_removal_user.side_effect = RuntimeError("unexpected bug")
        with (
            patch.object(remove_stale_zendesk_memberships, "retry") as retry,
            self.assertRaisesRegex(RuntimeError, "unexpected bug"),
        ):
            remove_stale_zendesk_memberships(*self.enqueue.call_args.args)
        retry.assert_not_called()
        self.zendesk.remove_organization_memberships.assert_not_called()

    def test_rollback_suppresses_cleanup_callback(self):
        self.user.groups.add(self.company.group)
        user_id = self.user.pk

        with transaction.atomic():
            self.user.delete()
            self.enqueue.assert_not_called()
            transaction.set_rollback(True)

        self.assertTrue(User.all_users.filter(pk=user_id).exists())
        self.assertTrue(Profile.all_profiles.filter(user_id=user_id, zendesk_id="201").exists())
        self.assertTrue(
            User.groups.through.objects.filter(user_id=user_id, group=self.company.group).exists()
        )
        self.enqueue.assert_not_called()
        self.client_class.assert_not_called()

    def test_cleanup_publish_failure_does_not_undo_committed_deletion(self):
        self.user.groups.add(self.company.group)
        user_id = self.user.pk
        self.enqueue.side_effect = RuntimeError("Broker unavailable")

        with self.assertLogs("django.db.backends.base", level="ERROR"):
            self.user.delete()

        self.assertFalse(User.all_users.filter(pk=user_id).exists())
        self.enqueue.assert_called_once_with(user_id, "201", ("101",))
        self.client_class.assert_not_called()
