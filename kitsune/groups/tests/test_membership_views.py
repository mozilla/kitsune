import time

from django.contrib import admin
from django.test import RequestFactory, override_settings
from django.urls import path
from pyquery import PyQuery as pq

from kitsune.groups.models import GroupProfile
from kitsune.groups.tests import GroupProfileFactory
from kitsune.sumo.tests import TestCase
from kitsune.sumo.urlresolvers import reverse
from kitsune.urls import urlpatterns as sumo_urlpatterns
from kitsune.users.tests import GroupFactory, UserFactory

urlpatterns = [
    path("admin/", admin.site.urls),
    *sumo_urlpatterns,
]


class EnterpriseMembershipFixtures:
    def setUp(self):
        super().setUp()
        self.root = GroupProfileFactory(
            slug="enterprise-root",
            visibility=GroupProfile.Visibility.PRIVATE,
            isolation_enabled=True,
        )
        self.company_a = self.child(self.root, "company-a")
        self.company_b = self.child(self.root, "company-b")
        self.team_a = self.child(self.company_a, "team-a")
        self.other_team_a = self.child(self.company_a, "other-team-a")
        self.nested_team_a = self.child(self.team_a, "nested-team-a")
        self.team_b = self.child(self.company_b, "team-b")
        self.unrelated = GroupProfileFactory(slug="unrelated-root")

    def child(self, parent, slug):
        return GroupProfile.objects.add_child(
            parent, create_kwargs={"group": GroupFactory(name=slug), "slug": slug}
        )

    def memberships(self, user):
        return set(user.groups.values_list("pk", flat=True))

    def tree_state(self):
        return list(
            GroupProfile.objects.order_by("pk").values_list(
                "pk",
                "group_id",
                "path",
                "depth",
                "numchild",
                "information",
                "information_html",
                "visibility",
                "isolation_enabled",
            )
        )


@override_settings(ENTERPRISE_GROUP_SLUG="enterprise-root", READ_ONLY=False)
class EnterpriseMembershipControlTests(EnterpriseMembershipFixtures, TestCase):
    def setUp(self):
        super().setUp()
        self.operator = UserFactory()
        self.root.leaders.add(self.operator)
        self.unrelated.leaders.add(self.operator)
        self.client.force_login(self.operator)

    def post_users(self, action, profile, *users):
        return self.client.post(
            reverse(f"groups.{action}", locale="en-US", args=[profile.slug]),
            {"users": ", ".join(user.username for user in users)},
        )

    def test_mixed_batch_shows_error_and_rolls_back_members_and_leaders(self):
        allowed = UserFactory(username="allowed-member")
        conflicting = UserFactory(username="conflicting-member")
        allowed.groups.add(self.other_team_a.group)
        conflicting.groups.add(self.team_b.group, self.root.group, self.unrelated.group)
        before = {user.pk: self.memberships(user) for user in (allowed, conflicting)}

        for action in ("add_member", "add_leader"):
            with self.subTest(action=action):
                response = self.post_users(action, self.team_a, allowed, conflicting)

                self.assertEqual(response.status_code, 200)
                errors = response.jinja_context["user_form"].errors.as_data()["users"]
                self.assertEqual([error.code for error in errors], ["company_conflict"])
                self.assertEqual(
                    pq(response.content)("#add-users-form .form-error.is-visible").attr("role"),
                    "alert",
                )
                self.assertIsNotNone(pq(response.content)("#toggle-add-users").attr("checked"))
                for user in (allowed, conflicting):
                    self.assertEqual(self.memberships(user), before[user.pk])
                    self.assertFalse(self.team_a.leaders.filter(pk=user.pk).exists())

    def test_same_company_departments_root_and_unrelated_memberships_remain_available(self):
        for action in ("add_member", "add_leader"):
            with self.subTest(action=action):
                member = UserFactory()
                member.groups.add(self.other_team_a.group)
                expected = {self.other_team_a.group_id}
                for profile in (self.team_a, self.nested_team_a, self.root, self.unrelated):
                    response = self.post_users(action, profile, member)

                    self.assertRedirects(
                        response, profile.get_absolute_url(), fetch_redirect_response=False
                    )
                    expected.add(profile.group_id)
                    self.assertEqual(self.memberships(member), expected)
                    if action == "add_leader":
                        self.assertTrue(profile.leaders.filter(pk=member.pk).exists())
                self.assertNotIn(self.company_a.group_id, self.memberships(member))

    def test_unauthorized_users_cannot_use_moderator_controls(self):
        ordinary_member = UserFactory()
        ordinary_member.groups.add(self.team_a.group)
        invitee = UserFactory()
        self.client.force_login(ordinary_member)
        response = self.client.get(self.team_a.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        self.assertFalse(pq(response.content)("#add-users-form"))

        for actor, status in ((ordinary_member, 403), (None, 302)):
            if actor is None:
                self.client.logout()
            for action in ("add_member", "add_leader"):
                with self.subTest(action=action, actor=actor):
                    response = self.post_users(action, self.team_a, invitee)
                    self.assertEqual(response.status_code, status)
                    self.assertEqual(self.memberships(invitee), set())
                    self.assertFalse(self.team_a.leaders.filter(pk=invitee.pk).exists())


@override_settings(
    ENTERPRISE_GROUP_SLUG="enterprise-root",
    READ_ONLY=False,
    ROOT_URLCONF=__name__,
)
class EnterpriseMembershipAdminTests(EnterpriseMembershipFixtures, TestCase):
    def setUp(self):
        super().setUp()
        self.operator = UserFactory(is_staff=True, is_superuser=True)
        self.root.leaders.add(self.operator)
        self.client.force_login(self.operator, backend="kitsune.users.auth.SumoOIDCAuthBackend")
        session = self.client.session
        session["oidc_id_token_expiration"] = time.time() + 3600
        session.save()

    def user_data(self, user, groups, **changes):
        return {
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
            "is_active": "on",
            "groups": [group.pk for group in groups],
            "user_permissions": [],
            "date_joined_0": user.date_joined.strftime("%Y-%m-%d"),
            "date_joined_1": user.date_joined.strftime("%H:%M:%S"),
            "_save": "Save",
            **changes,
        }

    def profile_data(self, profile, **changes):
        request = RequestFactory().get(
            reverse("admin:groups_groupprofile_change", args=[profile.pk])
        )
        request.user = self.operator
        form_class = admin.site._registry[GroupProfile].get_form(request, profile)
        form = form_class(instance=profile)
        return {
            "group": profile.group_id,
            "slug": profile.slug,
            "information": profile.information,
            "leaders": ",".join(str(pk) for pk in profile.leaders.values_list("pk", flat=True)),
            "treebeard_position": form["treebeard_position"].value(),
            "treebeard_ref_node": form["treebeard_ref_node"].value() or "",
            "_save": "Save",
            **changes,
        }

    def new_profile_data(self, group, member, reference, position):
        return {
            "group": group.pk,
            "leaders": str(member.pk),
            "visibility": GroupProfile.Visibility.PUBLIC,
            "isolation_enabled": "",
            "information": "",
            "treebeard_position": position,
            "treebeard_ref_node": reference.pk,
            "_save": "Save",
        }

    def assert_company_form_error(self, response):
        self.assertEqual(response.status_code, 200)
        form = response.context["adminform"].form
        errors = [
            error for field_errors in form.errors.as_data().values() for error in field_errors
        ]
        self.assertIn("company_conflict", [error.code for error in errors])

    def test_user_groups_replacement_rejects_two_companies_without_partial_user_save(self):
        member = UserFactory(first_name="Unchanged")
        member.groups.add(self.root.group, self.team_a.group, self.unrelated.group)
        before = self.memberships(member)

        response = self.client.post(
            reverse("admin:auth_user_change", args=[member.pk]),
            self.user_data(
                member,
                [
                    self.root.group,
                    self.company_a.group,
                    self.company_b.group,
                    self.unrelated.group,
                ],
                first_name="Rejected edit",
            ),
        )

        self.assert_company_form_error(response)
        self.assertEqual(self.memberships(member), before)
        member.refresh_from_db()
        self.assertEqual(member.first_name, "Unchanged")

    def test_user_groups_replacement_allows_explicit_transfer_and_removal(self):
        member = UserFactory()
        member.groups.add(
            self.company_a.group, self.team_a.group, self.root.group, self.unrelated.group
        )
        url = reverse("admin:auth_user_change", args=[member.pk])
        for groups in (
            [self.company_b.group, self.team_b.group, self.root.group, self.unrelated.group],
            [self.root.group, self.unrelated.group],
        ):
            with self.subTest(groups=groups):
                response = self.client.post(url, self.user_data(member, groups))
                self.assertEqual(response.status_code, 302)
                self.assertEqual(self.memberships(member), {group.pk for group in groups})

    def test_automatic_leader_membership_rolls_back_all_related_and_profile_changes(self):
        existing = UserFactory()
        existing.groups.add(self.team_a.group)
        self.team_a.leaders.add(existing)
        allowed = UserFactory()
        conflicting = UserFactory()
        allowed.groups.add(self.other_team_a.group)
        conflicting.groups.add(self.team_b.group)
        before = self.tree_state()
        memberships = {
            user.pk: self.memberships(user) for user in (existing, allowed, conflicting)
        }

        response = self.client.post(
            reverse("admin:groups_groupprofile_change", args=[self.team_a.pk]),
            self.profile_data(
                self.team_a,
                leaders=f"{existing.pk},{allowed.pk},{conflicting.pk}",
                information="Rejected leader edit",
            ),
        )

        self.assert_company_form_error(response)
        self.assertEqual(self.tree_state(), before)
        self.assertQuerySetEqual(self.team_a.leaders.all(), [existing])
        for user in (existing, allowed, conflicting):
            self.assertEqual(self.memberships(user), memberships[user.pk])

    def test_same_company_leader_is_automatically_added_as_member(self):
        member = UserFactory()
        member.groups.add(self.other_team_a.group)

        response = self.client.post(
            reverse("admin:groups_groupprofile_change", args=[self.team_a.pk]),
            self.profile_data(self.team_a, leaders=str(member.pk)),
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            self.memberships(member), {self.other_team_a.group_id, self.team_a.group_id}
        )
        self.assertQuerySetEqual(self.team_a.leaders.all(), [member])

    def test_add_root_siblings_preserves_existing_company_memberships(self):
        for position in ("left", "right"):
            with self.subTest(position=position):
                member = UserFactory()
                group = GroupFactory()
                member.groups.add(self.company_a.group, group)
                memberships = self.memberships(member)

                response = self.client.post(
                    reverse("admin:groups_groupprofile_add"),
                    self.new_profile_data(group, member, self.root, position),
                )

                self.assertEqual(response.status_code, 302)
                profile = GroupProfile.objects.get(group=group)
                self.root.refresh_from_db()
                self.assertIsNone(GroupProfile.objects.get_parent(profile))
                if position == "left":
                    self.assertLess(profile.path, self.root.path)
                else:
                    self.assertGreater(profile.path, self.root.path)
                self.assertEqual(profile.visibility, GroupProfile.Visibility.PUBLIC)
                self.assertFalse(profile.isolation_enabled)
                self.assertQuerySetEqual(profile.leaders.all(), [member])
                self.assertEqual(self.memberships(member), memberships)

    def test_add_company_siblings_rejects_conflicting_memberships_atomically(self):
        for position in ("left", "right"):
            with self.subTest(position=position):
                member = UserFactory()
                group = GroupFactory()
                member.groups.add(self.company_a.group, group)
                before = self.tree_state()
                memberships = self.memberships(member)

                response = self.client.post(
                    reverse("admin:groups_groupprofile_add"),
                    self.new_profile_data(group, member, self.company_a, position),
                )

                self.assert_company_form_error(response)
                self.assertEqual(self.tree_state(), before)
                self.assertEqual(self.memberships(member), memberships)

    def test_add_department_siblings_preserves_memberships_and_inherits_visibility(self):
        for position in ("left", "right"):
            with self.subTest(position=position):
                member = UserFactory()
                group = GroupFactory()
                member.groups.add(self.other_team_a.group, group)
                memberships = self.memberships(member)

                response = self.client.post(
                    reverse("admin:groups_groupprofile_add"),
                    self.new_profile_data(group, member, self.team_a, position),
                )

                self.assertEqual(response.status_code, 302)
                profile = GroupProfile.objects.get(group=group)
                self.team_a.refresh_from_db()
                self.assertEqual(GroupProfile.objects.get_parent(profile), self.company_a)
                if position == "left":
                    self.assertLess(profile.path, self.team_a.path)
                else:
                    self.assertGreater(profile.path, self.team_a.path)
                self.assertEqual(profile.visibility, self.root.visibility)
                self.assertFalse(profile.can_view(UserFactory(groups=[self.company_b.group])))
                self.assertQuerySetEqual(profile.leaders.all(), [member])
                self.assertEqual(self.memberships(member), memberships)

    def test_add_first_child_preserves_memberships_and_inherits_visibility(self):
        member = UserFactory()
        group = GroupFactory()
        member.groups.add(self.company_a.group, group)
        memberships = self.memberships(member)

        response = self.client.post(
            reverse("admin:groups_groupprofile_add"),
            self.new_profile_data(group, member, self.company_a, "first-child"),
        )

        self.assertEqual(response.status_code, 302)
        profile = GroupProfile.objects.get(group=group)
        self.assertEqual(GroupProfile.objects.get_parent(profile), self.company_a)
        self.assertIsNone(GroupProfile.objects.get_prev_sibling(profile))
        self.assertEqual(profile.visibility, self.root.visibility)
        self.assertFalse(profile.can_view(UserFactory(groups=[self.company_b.group])))
        self.assertQuerySetEqual(profile.leaders.all(), [member])
        self.assertEqual(self.memberships(member), memberships)

    def test_group_reassignment_cannot_attach_another_company_member(self):
        member = UserFactory()
        replacement_group = GroupFactory()
        member.groups.add(self.team_b.group, replacement_group)
        before = self.tree_state()
        memberships = self.memberships(member)

        response = self.client.post(
            reverse("admin:groups_groupprofile_change", args=[self.team_a.pk]),
            self.profile_data(
                self.team_a, group=replacement_group.pk, information="Rejected mapping edit"
            ),
        )

        self.assert_company_form_error(response)
        self.assertEqual(self.tree_state(), before)
        self.assertEqual(self.memberships(member), memberships)

    def test_move_form_rolls_back_descendant_conflict_and_earlier_profile_save(self):
        member = UserFactory()
        member.groups.add(self.company_a.group, self.nested_team_a.group)
        before = self.tree_state()
        memberships = self.memberships(member)

        response = self.client.post(
            reverse("admin:groups_groupprofile_change", args=[self.team_a.pk]),
            self.profile_data(
                self.team_a,
                treebeard_position="first-child",
                treebeard_ref_node=self.company_b.pk,
                information="Rejected move edit",
            ),
        )

        self.assert_company_form_error(response)
        self.assertEqual(self.tree_state(), before)
        self.assertEqual(self.memberships(member), memberships)

    def test_drag_drop_conflict_returns_bad_request_and_rolls_back(self):
        member = UserFactory()
        member.groups.add(self.company_a.group, self.nested_team_a.group)
        before = self.tree_state()
        memberships = self.memberships(member)
        changelist = reverse("admin:groups_groupprofile_changelist")

        response = self.client.post(
            f"{changelist}move/",
            {"node": self.team_a.pk, "target": self.company_b.pk, "relation": "child"},
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(self.tree_state(), before)
        self.assertEqual(self.memberships(member), memberships)

    def test_form_and_drag_drop_allow_moves_within_the_same_company(self):
        member = UserFactory()
        member.groups.add(self.team_a.group, self.other_team_a.group)
        memberships = self.memberships(member)

        response = self.client.post(
            reverse("admin:groups_groupprofile_change", args=[self.other_team_a.pk]),
            self.profile_data(
                self.other_team_a,
                treebeard_position="first-child",
                treebeard_ref_node=self.team_a.pk,
            ),
        )

        self.assertEqual(response.status_code, 302)
        self.other_team_a.refresh_from_db()
        self.assertEqual(GroupProfile.objects.get_parent(self.other_team_a), self.team_a)
        self.assertEqual(self.memberships(member), memberships)

        response = self.client.post(
            f"{reverse('admin:groups_groupprofile_changelist')}move/",
            {"node": self.other_team_a.pk, "target": self.company_a.pk, "relation": "child"},
        )

        self.assertEqual(response.status_code, 200)
        self.other_team_a.refresh_from_db()
        self.assertEqual(GroupProfile.objects.get_parent(self.other_team_a), self.company_a)
        self.assertEqual(self.memberships(member), memberships)
