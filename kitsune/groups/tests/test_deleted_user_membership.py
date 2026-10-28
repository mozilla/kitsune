from unittest.mock import call, patch

from django.contrib.auth.models import User
from django.db import transaction
from django.test import TransactionTestCase, override_settings

from kitsune.customercare.models import ZendeskOrganization
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

    def test_deletion_captures_all_linked_ids_after_commit_regardless_of_membership(self):
        other_company = EnterpriseCompanyFactory(root=self.root)
        ZendeskOrganization.objects.create(group_profile=other_company, zendesk_id="102")
        ZendeskOrganization.objects.create(group_profile=EnterpriseCompanyFactory(root=self.root))
        ZendeskOrganization.objects.create(
            group_profile=EnterpriseCompanyFactory(root=self.root), zendesk_id=""
        )
        for state, arrange in (
            ("no membership", lambda user: None),
            ("missing enterprise root", lambda user: None),
            ("department only", lambda user: user.groups.add(self.department.group)),
            ("root only", lambda user: user.groups.add(self.root.group)),
            ("company leader", self.company.leaders.add),
            (
                "ambiguous companies",
                lambda user: User.groups.through.objects.bulk_create(
                    User.groups.through(user=user, group=group)
                    for group in (self.company.group, other_company.group)
                ),
            ),
        ):
            with (
                self.subTest(state=state),
                override_settings(
                    ENTERPRISE_GROUP_SLUG=(
                        "missing-enterprise-root"
                        if state == "missing enterprise root"
                        else self.root.slug
                    )
                ),
            ):
                user = UserFactory(profile__zendesk_id="202")
                arrange(user)
                user_id = user.pk
                self.enqueue.reset_mock()

                with transaction.atomic():
                    user.delete()
                    self.enqueue.assert_not_called()

                self.enqueue.assert_called_once_with(user_id, "202", ("101", "102"))
        self.client_class.assert_not_called()

    def test_deletion_without_a_saved_remote_id_queues_no_cleanup(self):
        for missing, arrange in (
            (
                "remote id",
                lambda user: Profile.all_profiles.filter(user=user).update(zendesk_id=""),
            ),
            ("profile", lambda user: Profile.all_profiles.filter(user=user).delete()),
        ):
            with self.subTest(missing=missing):
                user = UserFactory(profile__zendesk_id="202")
                arrange(user)
                user.delete()
        self.enqueue.assert_not_called()
        self.client_class.assert_not_called()

    def test_leaving_then_deletion_before_sync_removes_only_the_captured_organization(self):
        self.user.groups.add(self.company.group)
        self.sync_enqueue.reset_mock()
        user_id = self.user.pk

        self.user.groups.remove(self.company.group)
        self.sync_enqueue.assert_called_once_with(user_id, removed_organization_ids=("101",))
        self.enqueue.reset_mock()
        with transaction.atomic():
            self.user.delete()
            self.mapping.delete()
        self.enqueue.assert_called_once_with(user_id, "201", ("101",))
        other_company = EnterpriseCompanyFactory(root=self.root)
        ZendeskOrganization.objects.create(group_profile=other_company, zendesk_id="102")

        sync_enterprise_zendesk_membership(*self.sync_enqueue.call_args.args)

        self.client_class.assert_not_called()

        remove_stale_zendesk_memberships(*self.enqueue.call_args.args)

        self.assertEqual(
            self.zendesk.method_calls,
            [
                call.validate_removal_user("201"),
                call.remove_organization_memberships(user_id="201", organization_ids={"101"}),
            ],
        )

    def test_removal_cleanup_survives_company_deletion_before_workers_run(self):
        self.user.groups.add(self.company.group)
        user_id = self.user.pk
        self.enqueue.reset_mock()

        with transaction.atomic():
            self.user.groups.remove(self.company.group)
            self.company.delete()
            self.enqueue.assert_not_called()

        self.enqueue.assert_called_once_with(user_id, "201", ("101",))
        remove_stale_zendesk_memberships(*self.enqueue.call_args.args)
        self.zendesk.remove_organization_memberships.assert_called_once_with(
            user_id="201", organization_ids={"101"}
        )

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
        self.assertFalse(Profile.all_profiles.filter(user_id=user_id).exists())
        self.assertFalse(User.groups.through.objects.filter(user_id=user_id).exists())
        self.enqueue.assert_called_once_with(user_id, "201", ("101",))
        self.client_class.assert_not_called()
