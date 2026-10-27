from io import StringIO
from unittest.mock import call, patch

import requests
from django.conf import settings
from django.core.management import CommandError, call_command
from django.db import OperationalError
from django.test import override_settings

from kitsune.customercare.zendesk import ZendeskProvisioningConflict
from kitsune.groups.tasks import sync_enterprise_zendesk_membership
from kitsune.groups.tests import DepartmentFactory, EnterpriseCompanyFactory, GroupProfileFactory
from kitsune.sumo.tests import TestCase
from kitsune.users.tests import UserFactory


@override_settings(ENTERPRISE_GROUP_SLUG="zendesk-reconcile-enterprise", READ_ONLY=False)
class SyncEnterpriseZendeskMembershipsTests(TestCase):
    def setUp(self):
        super().setUp()
        self.synchronize = self.enterContext(
            patch(
                "kitsune.groups.management.commands.sync_enterprise_zendesk_memberships."
                "sync_enterprise_zendesk_membership",
                return_value=None,
            )
        )
        self.output, self.errors = StringIO(), StringIO()

    def test_synchronizes_each_current_company_member_once(self):
        company = EnterpriseCompanyFactory()
        department = DepartmentFactory(company=company)
        nested_department = DepartmentFactory(company=department)
        other_company = EnterpriseCompanyFactory()
        direct_member = UserFactory()
        department_member = UserFactory()
        nested_member = UserFactory()
        inactive_member = UserFactory(is_active=False)
        direct_member.groups.add(company.group)
        department_member.groups.add(company.group, department.group, nested_department.group)
        nested_member.groups.add(nested_department.group)
        inactive_member.groups.add(other_company.group)

        call_command("sync_enterprise_zendesk_memberships", stdout=self.output)

        self.assertCountEqual(
            self.synchronize.call_args_list,
            [
                call(direct_member.pk),
                call(department_member.pk),
                call(nested_member.pk),
                call(inactive_member.pk),
            ],
        )
        self.assertIn("Synchronized: 4; failed: 0.", self.output.getvalue())

    def test_excludes_root_members_leaders_former_members_and_unrelated_users(self):
        root = GroupProfileFactory(slug=settings.ENTERPRISE_GROUP_SLUG)
        company = EnterpriseCompanyFactory(root=root)
        unrelated = GroupProfileFactory()
        unrelated_department = DepartmentFactory(company=unrelated)
        root.group.user_set.add(UserFactory())
        company.leaders.add(UserFactory())
        unrelated.group.user_set.add(UserFactory())
        unrelated_department.group.user_set.add(UserFactory())
        former_member = UserFactory()
        company.group.user_set.add(former_member)
        company.group.user_set.remove(former_member)
        UserFactory()

        call_command("sync_enterprise_zendesk_memberships", stdout=self.output)

        self.synchronize.assert_not_called()

    def test_missing_enterprise_root_synchronizes_nothing(self):
        unrelated = GroupProfileFactory()
        misplaced_root = DepartmentFactory(company=unrelated, slug=settings.ENTERPRISE_GROUP_SLUG)
        unrelated.group.user_set.add(UserFactory())
        misplaced_root.group.user_set.add(UserFactory())

        call_command("sync_enterprise_zendesk_memberships", stdout=self.output)

        self.synchronize.assert_not_called()

    def test_reports_failures_and_completes_remaining_members_without_queued_retries(self):
        company = EnterpriseCompanyFactory()
        members = UserFactory.create_batch(5)
        company.group.user_set.add(*members)
        members[-1].profile.delete()
        self.synchronize.side_effect = sync_enterprise_zendesk_membership
        unauthorized = requests.Response()
        unauthorized.status_code = 401

        with (
            patch("kitsune.groups.tasks.ZendeskClient", autospec=True) as client_class,
            patch.object(sync_enterprise_zendesk_membership, "apply_async") as enqueue,
            self.assertLogs("k.task", level="WARNING"),
            self.assertRaisesMessage(CommandError, "synchronization is incomplete"),
        ):
            client = client_class.return_value
            client.ensure_organization.return_value = "101"
            client.ensure_user.side_effect = (
                ZendeskProvisioningConflict("account_conflict"),
                requests.HTTPError(
                    "401 Client Error: Unauthorized for url: https://support.zendesk.com/api/v2/"
                    f"users/search.json?query=email:%22{members[1].email}%22",
                    response=unauthorized,
                ),
                OperationalError("private deadlock details"),
                "201",
            )
            client.get_organization_memberships.return_value = []
            call_command(
                "sync_enterprise_zendesk_memberships", stdout=self.output, stderr=self.errors
            )

        self.assertEqual(self.synchronize.call_args_list, [call(member.pk) for member in members])
        self.assertEqual(
            self.errors.getvalue().splitlines(),
            [
                f"User {members[0].pk}: account_conflict.",
                f"User {members[1].pk}: ZendeskUnavailable HTTPError 401.",
                f"User {members[2].pk}: OperationalError.",
                f"User {members[4].pk}: profile_missing.",
            ],
        )
        self.assertIn(f"Synchronized user {members[3].pk}.", self.output.getvalue())
        self.assertIn("Synchronized: 1; failed: 4.", self.output.getvalue())
        enqueue.assert_not_called()

    @override_settings(READ_ONLY=True)
    def test_read_only_mode_reports_failure_without_synchronizing(self):
        with self.assertRaisesMessage(CommandError, "read-only mode"):
            call_command("sync_enterprise_zendesk_memberships", stdout=self.output)
        self.synchronize.assert_not_called()
