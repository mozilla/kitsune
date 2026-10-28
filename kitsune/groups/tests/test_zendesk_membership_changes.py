import time
from unittest.mock import ANY, call, patch

from django.contrib import admin
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.db import transaction
from django.test import RequestFactory, override_settings
from django.urls import path, reverse

from kitsune.customercare.models import ZendeskOrganization
from kitsune.groups.models import GroupProfile
from kitsune.groups.tests import DepartmentFactory, EnterpriseCompanyFactory, GroupProfileFactory
from kitsune.products.tests import SupportCoverageFactory
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
        self.tag = self.enterContext(
            patch("kitsune.customercare.tasks.tag_revoked_chat_tickets.delay")
        )
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

    def test_hierarchy_changes_queue_affected_members_after_commit(self):
        def company_group_deletion():
            other = UserFactory()
            self.user.groups.add(self.company.group, self.department.group)
            other.groups.add(self.department.group)
            ZendeskOrganization.objects.create(group_profile=self.company, zendesk_id="101")
            return self.company.group.delete, [
                call(self.user.pk, removed_organization_ids=("101",)),
                call(other.pk, removed_organization_ids=("101",)),
            ]

        def former_company_group_deletion():
            self.user.groups.add(self.department.group)
            ZendeskOrganization.objects.create(group_profile=self.company, zendesk_id="101")
            GroupProfile.objects.move(self.company, GroupProfileFactory(), "last-child")
            return self.company.group.delete, [
                call(self.user.pk, removed_organization_ids=("101",))
            ]

        def department_group_deletion():
            self.user.groups.add(self.company.group, self.department.group)
            return self.department.group.delete, [call(self.user.pk)]

        def company_profile_deletion():
            self.user.groups.add(self.company.group)
            ZendeskOrganization.objects.create(group_profile=self.company, zendesk_id="101")
            return self.company.delete, [call(self.user.pk, removed_organization_ids=("101",))]

        def profile_queryset_deletion_with_a_shared_group():
            DepartmentFactory(company=GroupProfileFactory(), group=self.department.group)
            self.user.groups.add(self.department.group)
            return GroupProfile.objects.filter(pk=self.company.pk).delete, [call(self.user.pk)]

        def overlapping_bulk_group_deletion():
            self.user.groups.add(self.company.group, self.department.group)
            groups = Group.objects.filter(pk__in=[self.company.group_id, self.department.group_id])
            return groups.delete, [call(self.user.pk)]

        def root_profile_deletion():
            other_company = EnterpriseCompanyFactory(root=self.root)
            other = UserFactory()
            self.user.groups.add(self.department.group)
            other.groups.add(other_company.group)
            ZendeskOrganization.objects.create(group_profile=self.company, zendesk_id="101")
            ZendeskOrganization.objects.create(group_profile=other_company, zendesk_id="102")
            return self.root.delete, [
                call(self.user.pk, removed_organization_ids=("101", "102")),
                call(other.pk, removed_organization_ids=("101", "102")),
            ]

        def unrelated_group_deletion():
            unrelated = GroupProfileFactory()
            self.user.groups.add(unrelated.group)
            return unrelated.group.delete, []

        def department_move_between_companies():
            other_company = EnterpriseCompanyFactory(root=self.root)
            nested = DepartmentFactory(company=self.department)
            self.user.groups.add(self.department.group, nested.group)
            return (
                lambda: GroupProfile.objects.move(self.department, other_company, "last-child"),
                [call(self.user.pk)],
            )

        def subtree_move_into_a_company():
            team = DepartmentFactory(company=GroupProfileFactory())
            self.user.groups.add(team.group)
            return (
                lambda: GroupProfile.objects.move(team, self.company, "last-child"),
                [call(self.user.pk)],
            )

        def subtree_move_out_of_the_tree():
            outside = GroupProfileFactory()
            self.user.groups.add(self.department.group)
            return (
                lambda: GroupProfile.objects.move(self.department, outside, "last-child"),
                [call(self.user.pk)],
            )

        def move_within_a_company():
            sibling = DepartmentFactory(company=self.company)
            self.user.groups.add(self.department.group)
            return lambda: GroupProfile.objects.move(self.department, sibling, "last-child"), []

        def child_profile_for_a_group_with_members():
            group = GroupFactory()
            group.user_set.add(self.user)
            return (
                lambda: GroupProfile.objects.add_child(
                    self.company, create_kwargs={"group": group, "slug": "new-department"}
                ),
                [call(self.user.pk)],
            )

        def sibling_profile_for_a_group_with_members():
            group = GroupFactory()
            group.user_set.add(self.user)
            return (
                lambda: GroupProfile.objects.add_sibling(
                    self.company, "left", create_kwargs={"group": group, "slug": "new-company"}
                ),
                [call(self.user.pk)],
            )

        for arrange in (
            company_group_deletion,
            former_company_group_deletion,
            department_group_deletion,
            company_profile_deletion,
            profile_queryset_deletion_with_a_shared_group,
            overlapping_bulk_group_deletion,
            root_profile_deletion,
            unrelated_group_deletion,
            department_move_between_companies,
            subtree_move_into_a_company,
            subtree_move_out_of_the_tree,
            move_within_a_company,
            child_profile_for_a_group_with_members,
            sibling_profile_for_a_group_with_members,
        ):
            with self.subTest(arrange.__name__), transaction.atomic():
                # Rolled-back cases leave stale paths and deleted groups cached on these objects.
                for profile in (self.root, self.company, self.department):
                    profile.refresh_from_db()
                operation, expected = arrange()
                self.enqueue.reset_mock()
                with self.captureOnCommitCallbacks(execute=True):
                    operation()
                    self.enqueue.assert_not_called()
                self.assertCountEqual(self.enqueue.call_args_list, expected)
                transaction.set_rollback(True)
        self.client_class.assert_not_called()

    def test_rolled_back_or_rejected_changes_queue_nothing(self):
        outside = GroupProfileFactory()
        other_company = EnterpriseCompanyFactory(root=self.root)
        group = GroupFactory()
        group.user_set.add(self.user)
        self.user.groups.add(self.company.group, self.department.group)
        for change, operation in (
            ("addition", lambda: UserFactory().groups.add(self.company.group)),
            ("reverse clear", self.department.group.user_set.clear),
            ("forward clear", self.user.groups.clear),
            ("group deletion", self.company.group.delete),
            ("move", lambda: GroupProfile.objects.move(self.department, outside, "last-child")),
            (
                "insertion",
                lambda: GroupProfile.objects.add_child(
                    self.company, create_kwargs={"group": group, "slug": "rolled-back-department"}
                ),
            ),
            (
                "rejected move",
                lambda: GroupProfile.objects.move(self.department, other_company, "last-child"),
            ),
        ):
            with self.subTest(change=change), self.captureOnCommitCallbacks(execute=True):
                with self.assertRaises((ValueError, ValidationError)), transaction.atomic():
                    operation()
                    raise ValueError("roll back the change")
            self.enqueue.assert_not_called()
            self.assertQuerySetEqual(
                GroupProfile.objects.enterprise_companies(self.user), [self.company]
            )
        self.client_class.assert_not_called()

    def include_chat(self):
        SupportCoverageFactory(contract__company=self.company, includes_chat=True)

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

    def test_admin_reassignment_tags_chats_of_members_who_leave_the_company(self):
        self.include_chat()
        replacement = GroupFactory()
        staying = UserFactory(profile__zendesk_id="202")
        self.user.groups.add(self.department.group)
        staying.groups.add(self.department.group, replacement)
        with self.captureOnCommitCallbacks(execute=True):
            response = self.admin_reassign(replacement)
            self.tag.assert_not_called()
        self.assertEqual(response.status_code, 302)
        self.tag.assert_called_once_with("201", product_slugs=None, before=ANY)

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
        self.include_chat()
        self.user.groups.add(self.department.group)
        other_company = EnterpriseCompanyFactory(root=self.root)
        other = UserFactory()
        other.groups.add(other_company.group)
        with self.captureOnCommitCallbacks(execute=True):
            response = self.admin_reassign(other_company.group)
        self.assertEqual(response.status_code, 200)
        self.enqueue.assert_not_called()
        self.tag.assert_not_called()
        self.assertQuerySetEqual(
            GroupProfile.objects.enterprise_companies(self.user), [self.company]
        )
