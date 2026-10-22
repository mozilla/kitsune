import time
from unittest.mock import call, patch

from django.contrib import admin
from django.contrib.auth.models import Group, User
from django.core.exceptions import ValidationError
from django.db import transaction
from django.test import RequestFactory, override_settings
from django.urls import path, reverse

from kitsune.customercare.models import ZendeskOrganization
from kitsune.groups.models import GroupProfile
from kitsune.groups.tasks import sync_enterprise_zendesk_membership
from kitsune.groups.tests import DepartmentFactory, EnterpriseCompanyFactory, GroupProfileFactory
from kitsune.sumo.tests import TestCase
from kitsune.urls import urlpatterns as sumo_urlpatterns
from kitsune.users.tests import GroupFactory, UserFactory

urlpatterns = [path("admin/", admin.site.urls), *sumo_urlpatterns]


@override_settings(
    ENTERPRISE_GROUP_SLUG="membership-changes-root", READ_ONLY=False, ROOT_URLCONF=__name__
)
class EnterpriseZendeskMembershipChangesTests(TestCase):
    def setUp(self):
        super().setUp()
        self.enqueue = self.enterContext(
            patch("kitsune.groups.tasks.sync_enterprise_zendesk_membership.delay")
        )
        self.enterContext(patch("kitsune.groups.tasks.remove_stale_zendesk_memberships.delay"))
        self.client_class = self.enterContext(
            patch("kitsune.groups.tasks.ZendeskClient", autospec=True)
        )
        self.zendesk = self.client_class.return_value
        self.zendesk.ensure_user.return_value = "201"
        self.zendesk.validate_removal_user.return_value = "201"
        self.root = GroupProfileFactory(slug="membership-changes-root")
        self.company = EnterpriseCompanyFactory(root=self.root)
        self.department = DepartmentFactory(company=self.company)
        self.user = UserFactory(profile__zendesk_id="201")

    def test_company_group_deletion_captures_remote_id_for_all_members_once(self):
        other = UserFactory()
        self.user.groups.add(self.company.group, self.department.group)
        other.groups.add(self.department.group)
        mapping = ZendeskOrganization.objects.create(group_profile=self.company, zendesk_id="101")

        with self.captureOnCommitCallbacks(execute=True), transaction.atomic():
            self.company.group.delete()
            self.enqueue.assert_not_called()
            self.client_class.assert_not_called()

        self.assertCountEqual(
            self.enqueue.call_args_list,
            [
                call(self.user.pk, removed_organization_ids=("101",)),
                call(other.pk, removed_organization_ids=("101",)),
            ],
        )
        self.assertFalse(ZendeskOrganization.objects.filter(pk=mapping.pk).exists())
        sync_enterprise_zendesk_membership(self.user.pk, removed_organization_ids=("101",))
        self.zendesk.remove_organization_memberships.assert_called_once_with(
            user_id="201", organization_ids={"101"}
        )
        self.zendesk.ensure_organization_membership.assert_not_called()

    def test_moved_former_company_deletion_captures_retained_mapping(self):
        outside = GroupProfileFactory()
        self.user.groups.add(self.department.group)
        mapping = ZendeskOrganization.objects.create(group_profile=self.company, zendesk_id="101")
        with self.captureOnCommitCallbacks(execute=True):
            GroupProfile.objects.move(self.company, outside, "last-child")
        self.assertFalse(GroupProfile.objects.enterprise_companies(self.user).exists())
        self.assertTrue(ZendeskOrganization.objects.filter(pk=mapping.pk).exists())
        self.enqueue.reset_mock()

        with self.captureOnCommitCallbacks(execute=True), transaction.atomic():
            self.company.group.delete()
            self.enqueue.assert_not_called()
            self.client_class.assert_not_called()

        self.enqueue.assert_called_once_with(self.user.pk, removed_organization_ids=("101",))
        self.assertFalse(ZendeskOrganization.objects.filter(pk=mapping.pk).exists())

    def test_department_group_deletion_reconciles_surviving_company_membership(self):
        self.user.groups.add(self.company.group, self.department.group)
        with self.captureOnCommitCallbacks(execute=True), transaction.atomic():
            self.department.group.delete()
            self.enqueue.assert_not_called()
            self.client_class.assert_not_called()

        self.enqueue.assert_called_once_with(self.user.pk)
        self.assertQuerySetEqual(
            GroupProfile.objects.enterprise_companies(self.user), [self.company]
        )

    def test_direct_company_profile_deletion_preserves_group_but_captures_remote_id(self):
        self.user.groups.add(self.company.group)
        ZendeskOrganization.objects.create(group_profile=self.company, zendesk_id="101")
        group_id = self.company.group_id
        company_id = self.company.pk
        with self.captureOnCommitCallbacks(execute=True):
            self.company.delete()
            self.enqueue.assert_not_called()

        self.enqueue.assert_called_once_with(self.user.pk, removed_organization_ids=("101",))
        self.assertTrue(
            User.groups.through.objects.filter(user=self.user, group_id=group_id).exists()
        )
        self.assertFalse(GroupProfile.objects.filter(pk=company_id).exists())
        self.assertFalse(GroupProfile.objects.enterprise_companies(self.user).exists())

    def test_profile_queryset_deletion_preserves_shared_groups_and_enqueues_members(self):
        outside = GroupProfileFactory()
        shared = DepartmentFactory(company=outside, group=self.department.group)
        self.user.groups.add(self.department.group)
        with self.captureOnCommitCallbacks(execute=True):
            GroupProfile.objects.filter(pk=self.company.pk).delete()
            self.enqueue.assert_not_called()

        self.enqueue.assert_called_once_with(self.user.pk)
        self.assertTrue(Group.objects.filter(pk=self.department.group_id).exists())
        self.assertTrue(GroupProfile.objects.filter(pk=shared.pk).exists())
        self.assertFalse(GroupProfile.objects.enterprise_companies(self.user).exists())

    def test_bulk_group_deletion_handles_overlapping_subtrees(self):
        self.user.groups.add(self.company.group, self.department.group)
        with self.captureOnCommitCallbacks(execute=True):
            Group.objects.filter(pk__in=[self.company.group_id, self.department.group_id]).delete()
        self.enqueue.assert_called_once_with(self.user.pk)
        self.assertFalse(GroupProfile.objects.enterprise_companies(self.user).exists())

    def test_root_profile_deletion_captures_every_deleted_company_mapping(self):
        other_company = EnterpriseCompanyFactory(root=self.root)
        other_user = UserFactory()
        self.user.groups.add(self.department.group)
        other_user.groups.add(other_company.group)
        ZendeskOrganization.objects.create(group_profile=self.company, zendesk_id="101")
        ZendeskOrganization.objects.create(group_profile=other_company, zendesk_id="102")
        with self.captureOnCommitCallbacks(execute=True):
            self.root.delete()

        self.assertCountEqual(
            self.enqueue.call_args_list,
            [
                call(self.user.pk, removed_organization_ids=("101", "102")),
                call(other_user.pk, removed_organization_ids=("101", "102")),
            ],
        )
        self.assertFalse(ZendeskOrganization.objects.exists())

    def test_unrelated_group_deletion_does_not_enqueue(self):
        unrelated = GroupProfileFactory()
        self.user.groups.add(unrelated.group)
        with self.captureOnCommitCallbacks(execute=True):
            unrelated.group.delete()
        self.enqueue.assert_not_called()

    def test_department_move_between_companies_enqueues_current_company(self):
        other_company = EnterpriseCompanyFactory(root=self.root)
        nested = DepartmentFactory(company=self.department)
        self.user.groups.add(self.department.group, nested.group)
        with self.captureOnCommitCallbacks(execute=True), transaction.atomic():
            GroupProfile.objects.move(self.department, other_company, "last-child")
            self.enqueue.assert_not_called()
            self.client_class.assert_not_called()

        self.enqueue.assert_called_once_with(self.user.pk)
        self.assertQuerySetEqual(
            GroupProfile.objects.enterprise_companies(self.user), [other_company]
        )

    def test_subtree_moves_into_and_out_of_enterprise_tree_enqueue(self):
        outside = GroupProfileFactory()
        team = DepartmentFactory(company=outside)
        self.user.groups.add(team.group)
        for destination, companies in ((self.company, [self.company]), (outside, [])):
            with self.subTest(destination=destination.pk):
                self.enqueue.reset_mock()
                with self.captureOnCommitCallbacks(execute=True):
                    GroupProfile.objects.move(team, destination, "last-child")
                    self.enqueue.assert_not_called()
                    self.client_class.assert_not_called()
                self.enqueue.assert_called_once_with(self.user.pk)
                self.assertQuerySetEqual(
                    GroupProfile.objects.enterprise_companies(self.user), companies
                )

    def test_move_within_company_does_not_enqueue_unchanged_membership(self):
        sibling = DepartmentFactory(company=self.company)
        self.user.groups.add(self.department.group)
        with self.captureOnCommitCallbacks(execute=True):
            GroupProfile.objects.move(self.department, sibling, "last-child")
        self.enqueue.assert_not_called()

    def test_add_child_with_existing_group_members_enqueues(self):
        group = GroupFactory()
        group.user_set.add(self.user)
        with self.captureOnCommitCallbacks(execute=True):
            GroupProfile.objects.add_child(
                self.company, create_kwargs={"group": group, "slug": "new-department"}
            )
            self.enqueue.assert_not_called()
            self.client_class.assert_not_called()
        self.enqueue.assert_called_once_with(self.user.pk)
        self.assertQuerySetEqual(
            GroupProfile.objects.enterprise_companies(self.user), [self.company]
        )

    def test_add_sibling_with_existing_group_members_enqueues(self):
        group = GroupFactory()
        group.user_set.add(self.user)
        with self.captureOnCommitCallbacks(execute=True):
            company = GroupProfile.objects.add_sibling(
                self.company,
                "left",
                create_kwargs={"group": group, "slug": "new-company"},
            )
            self.enqueue.assert_not_called()
        self.enqueue.assert_called_once_with(self.user.pk)
        self.assertQuerySetEqual(GroupProfile.objects.enterprise_companies(self.user), [company])

    def test_rollback_discards_clear_deletion_move_and_insertion_callbacks(self):
        outside = GroupProfileFactory()
        group = GroupFactory()
        group.user_set.add(self.user)
        self.user.groups.add(self.department.group)
        operations = (
            self.department.group.user_set.clear,
            self.user.groups.clear,
            self.company.group.delete,
            lambda: GroupProfile.objects.move(self.department, outside, "last-child"),
            lambda: GroupProfile.objects.add_child(
                self.company, create_kwargs={"group": group, "slug": "rolled-back-department"}
            ),
        )
        for operation in operations:
            with self.subTest(operation=operation), self.captureOnCommitCallbacks(execute=True):
                with self.assertRaises(ValueError), transaction.atomic():
                    operation()
                    raise ValueError("roll back hierarchy change")
            self.enqueue.assert_not_called()
            self.assertQuerySetEqual(
                GroupProfile.objects.enterprise_companies(self.user), [self.company]
            )
        self.client_class.assert_not_called()

    def test_rejected_company_move_does_not_enqueue(self):
        other_company = EnterpriseCompanyFactory(root=self.root)
        self.user.groups.add(self.company.group, self.department.group)
        with self.captureOnCommitCallbacks(execute=True), self.assertRaises(ValidationError):
            GroupProfile.objects.move(self.department, other_company, "last-child")
        self.enqueue.assert_not_called()
        self.assertQuerySetEqual(
            GroupProfile.objects.enterprise_companies(self.user), [self.company]
        )

    def admin_reassign(self, group, **changes):
        operator = UserFactory(is_staff=True, is_superuser=True)
        self.client.force_login(operator, backend="kitsune.users.auth.SumoOIDCAuthBackend")
        session = self.client.session
        session["oidc_id_token_expiration"] = time.time() + 3600
        session.save()
        url = reverse("admin:groups_groupprofile_change", args=[self.department.pk])
        request = RequestFactory().get(url)
        request.user = operator
        form_class = admin.site._registry[GroupProfile].get_form(request, self.department)
        form = form_class(instance=self.department)
        return self.client.post(
            url,
            {
                "group": group.pk,
                "information": self.department.information,
                "leaders": "",
                "treebeard_position": form["treebeard_position"].value(),
                "treebeard_ref_node": form["treebeard_ref_node"].value() or "",
                "_save": "Save",
                **changes,
            },
        )

    def test_admin_reassignment_enqueues_old_and_new_group_members(self):
        self.user.groups.add(self.department.group)
        replacement = GroupFactory()
        other = UserFactory()
        other.groups.add(replacement)
        with self.captureOnCommitCallbacks(execute=True):
            response = self.admin_reassign(replacement)
            self.enqueue.assert_not_called()
            self.client_class.assert_not_called()

        self.assertEqual(response.status_code, 302)
        self.assertCountEqual(self.enqueue.call_args_list, [call(self.user.pk), call(other.pk)])
        self.assertFalse(GroupProfile.objects.enterprise_companies(self.user).exists())
        self.assertQuerySetEqual(GroupProfile.objects.enterprise_companies(other), [self.company])

    def test_admin_reassignment_and_move_out_enqueues_former_members(self):
        self.user.groups.add(self.department.group)
        outside = GroupProfileFactory()
        replacement = GroupFactory()
        with self.captureOnCommitCallbacks(execute=True):
            response = self.admin_reassign(
                replacement, treebeard_ref_node=outside.pk, treebeard_position="first-child"
            )
        self.assertEqual(response.status_code, 302)
        self.enqueue.assert_called_once_with(self.user.pk)
        self.assertFalse(GroupProfile.objects.enterprise_companies(self.user).exists())

    def test_rejected_admin_reassignment_discards_old_member_callback(self):
        self.user.groups.add(self.department.group)
        other_company = EnterpriseCompanyFactory(root=self.root)
        other = UserFactory()
        other.groups.add(other_company.group)
        with self.captureOnCommitCallbacks(execute=True):
            response = self.admin_reassign(other_company.group)
        self.assertEqual(response.status_code, 200)
        self.enqueue.assert_not_called()
        self.assertQuerySetEqual(
            GroupProfile.objects.enterprise_companies(self.user), [self.company]
        )
