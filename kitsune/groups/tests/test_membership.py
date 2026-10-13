from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from threading import Barrier, Event
from unittest.mock import patch
from uuid import uuid4

from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import connections, transaction
from django.test import TransactionTestCase, override_settings

from kitsune.groups import membership
from kitsune.groups.membership import validate_enterprise_memberships
from kitsune.groups.models import GroupProfile
from kitsune.groups.tests import GroupProfileFactory
from kitsune.sumo.tests import TestCase
from kitsune.users.tests import GroupFactory, UserFactory


class MembershipFixtures:
    def setUp(self):
        super().setUp()
        self.root = GroupProfileFactory(
            slug=settings.ENTERPRISE_GROUP_SLUG,
            visibility=GroupProfile.Visibility.PRIVATE,
        )
        self.company_a = self.child(self.root)
        self.company_b = self.child(self.root)
        self.team_a = self.child(self.company_a)
        self.team_b = self.child(self.company_b)
        self.other_team_a = self.child(self.company_a)
        self.nested_a = self.child(self.team_a)
        self.unrelated = GroupProfileFactory()
        self.user = UserFactory()

    def child(self, parent, **kwargs):
        if "group" not in kwargs:
            kwargs["group"] = GroupFactory()
        return GroupProfile.objects.add_child(
            parent, create_kwargs={"slug": str(uuid4()), **kwargs}
        )

    def memberships(self, user):
        return set(
            User.groups.through.objects.filter(user_id=user.pk).values_list("group_id", flat=True)
        )

    def tree_state(self):
        return list(
            GroupProfile.objects.order_by("pk").values_list("pk", "path", "depth", "numchild")
        )

    def add_legacy_conflict(self, user):
        # Model old data explicitly; application additions must not create this state.
        User.groups.through.objects.bulk_create(
            [
                User.groups.through(user_id=user.pk, group_id=self.company_a.group_id),
                User.groups.through(user_id=user.pk, group_id=self.company_b.group_id),
            ]
        )

    def assert_company_conflict(self, operation):
        with self.assertRaises(ValidationError) as caught, transaction.atomic():
            operation()
        self.assertEqual(caught.exception.code, "company_conflict")


@override_settings(ENTERPRISE_GROUP_SLUG="membership-enterprise-root")
class EnterpriseMembershipTests(MembershipFixtures, TestCase):
    def test_direct_and_indirect_memberships_cannot_cross_companies(self):
        for first, second in (
            (self.company_a, self.company_b),
            (self.company_a, self.team_b),
            (self.team_a, self.company_b),
            (self.team_a, self.team_b),
            (self.nested_a, self.team_b),
        ):
            with self.subTest(first=first.pk, second=second.pk):
                user = UserFactory()
                user.groups.add(first.group)
                self.assert_company_conflict(lambda: user.groups.add(second.group))
                self.assertEqual(self.memberships(user), {first.group_id})

    def test_multiple_departments_and_nested_teams_within_one_company_are_allowed(self):
        profiles = (self.company_a, self.team_a, self.other_team_a, self.nested_a)
        self.user.groups.add(*(profile.group for profile in profiles))
        self.assertEqual(self.memberships(self.user), {profile.group_id for profile in profiles})

    def test_department_membership_does_not_enroll_company_or_root(self):
        self.user.groups.add(self.team_a.group, self.nested_a.group)
        self.assertEqual(
            self.memberships(self.user), {self.team_a.group_id, self.nested_a.group_id}
        )

    def test_forward_multi_company_batch_is_rejected_in_full(self):
        self.assert_company_conflict(
            lambda: self.user.groups.add(
                self.team_a.group, self.team_b.group, self.unrelated.group
            )
        )
        self.assertEqual(self.memberships(self.user), set())

    def test_reverse_batch_is_rejected_for_every_requested_user(self):
        eligible = UserFactory()
        self.user.groups.add(self.team_a.group)
        self.assert_company_conflict(lambda: self.team_b.group.user_set.add(eligible, self.user))
        self.assertEqual(self.memberships(eligible), set())
        self.assertEqual(self.memberships(self.user), {self.team_a.group_id})

    def test_forward_set_rolls_back_its_removals_when_addition_conflicts(self):
        self.user.groups.add(self.company_a.group, self.unrelated.group)
        self.assert_company_conflict(
            lambda: self.user.groups.set([self.company_a.group, self.team_b.group])
        )
        self.assertEqual(
            self.memberships(self.user), {self.company_a.group_id, self.unrelated.group_id}
        )

    def test_reverse_set_rolls_back_removal_of_existing_members(self):
        existing = UserFactory()
        self.team_b.group.user_set.add(existing)
        self.user.groups.add(self.company_a.group)
        self.assert_company_conflict(lambda: self.team_b.group.user_set.set([self.user]))
        self.assertEqual(self.memberships(existing), {self.team_b.group_id})
        self.assertEqual(self.memberships(self.user), {self.company_a.group_id})

    def test_replacement_can_remove_old_company_and_choose_one_new_company(self):
        self.user.groups.add(self.company_a.group, self.team_a.group)
        validate_enterprise_memberships(
            [self.user.pk], [self.company_b.group_id, self.team_b.group_id], replace=True
        )
        self.user.groups.set([self.company_b.group, self.team_b.group])
        self.assertEqual(
            self.memberships(self.user), {self.company_b.group_id, self.team_b.group_id}
        )

    def test_full_replacement_validation_rejects_two_companies(self):
        self.assert_company_conflict(
            lambda: validate_enterprise_memberships(
                [self.user.pk], [self.team_a.group_id, self.team_b.group_id], replace=True
            )
        )
        self.assertEqual(self.memberships(self.user), set())

    def test_staff_superusers_have_no_membership_bypass(self):
        staff = UserFactory(is_staff=True, is_superuser=True)
        self.root.leaders.add(staff)
        staff.groups.add(self.team_a.group)
        self.assert_company_conflict(lambda: staff.groups.add(self.company_b.group))
        self.assertEqual(self.memberships(staff), {self.team_a.group_id})

    def test_root_membership_leadership_and_other_trees_are_unchanged(self):
        other_company = self.child(self.unrelated)
        other_team = self.child(other_company)
        self.root.leaders.add(self.user)
        self.company_b.leaders.add(self.user)
        profiles = (self.root, self.team_a, self.unrelated, other_company, other_team)
        self.user.groups.add(*(profile.group for profile in profiles))
        self.assertEqual(self.memberships(self.user), {profile.group_id for profile in profiles})
        self.assertTrue(self.root.leaders.filter(pk=self.user.pk).exists())
        self.assertTrue(self.company_b.leaders.filter(pk=self.user.pk).exists())

    def test_legacy_conflict_blocks_new_enterprise_additions_but_not_unrelated_ones(self):
        self.add_legacy_conflict(self.user)
        self.user.groups.add(self.root.group, self.unrelated.group)
        self.assert_company_conflict(lambda: self.user.groups.add(self.team_a.group))
        self.assertEqual(
            self.memberships(self.user),
            {
                self.company_a.group_id,
                self.company_b.group_id,
                self.root.group_id,
                self.unrelated.group_id,
            },
        )

    def test_removals_can_resolve_a_legacy_conflict(self):
        self.add_legacy_conflict(self.user)
        self.company_b.group.user_set.remove(self.user)
        self.user.groups.add(self.team_a.group)
        self.assertEqual(
            self.memberships(self.user), {self.company_a.group_id, self.team_a.group_id}
        )
        self.user.groups.clear()
        self.user.groups.add(self.team_b.group)
        self.assertEqual(self.memberships(self.user), {self.team_b.group_id})

    def test_all_profiles_of_a_group_count_toward_its_membership(self):
        self.child(self.company_b, group=self.team_a.group)
        self.assert_company_conflict(lambda: self.user.groups.add(self.team_a.group))
        self.assertEqual(self.memberships(self.user), set())

    def test_aliases_within_one_company_do_not_create_false_conflicts(self):
        self.child(self.other_team_a, group=self.team_a.group)
        self.user.groups.add(self.company_a.group, self.team_a.group)
        self.assertEqual(
            self.memberships(self.user), {self.company_a.group_id, self.team_a.group_id}
        )

    def test_new_profile_cannot_assign_existing_members_to_a_second_company(self):
        self.user.groups.add(self.team_a.group)
        before = self.tree_state()
        self.assert_company_conflict(lambda: self.child(self.company_b, group=self.team_a.group))
        self.assertEqual(self.tree_state(), before)
        self.assertEqual(self.memberships(self.user), {self.team_a.group_id})

    def test_conflicting_sibling_creation_rolls_back_existing_company_paths(self):
        self.user.groups.add(self.company_a.group, self.team_a.group)
        before = self.tree_state()
        self.assert_company_conflict(
            lambda: GroupProfile.objects.add_sibling(
                self.company_a,
                "left",
                create_kwargs={"group": self.team_a.group, "slug": "conflicting-sibling"},
            )
        )
        self.assertEqual(self.tree_state(), before)
        self.assertEqual(
            self.memberships(self.user), {self.company_a.group_id, self.team_a.group_id}
        )

    def test_configured_slug_below_another_root_does_not_define_enterprise_tree(self):
        GroupProfile.objects.move(self.root, self.unrelated, "last-child")
        self.user.groups.add(self.company_a.group, self.company_b.group)
        self.assertEqual(
            self.memberships(self.user), {self.company_a.group_id, self.company_b.group_id}
        )


@override_settings(ENTERPRISE_GROUP_SLUG="membership-enterprise-root")
class EnterpriseHierarchyTests(MembershipFixtures, TestCase):
    def test_cross_company_move_rolls_back_paths_counts_and_memberships(self):
        self.user.groups.add(self.company_a.group, self.nested_a.group)
        before = self.tree_state()
        old_path = self.team_a.path
        self.assert_company_conflict(
            lambda: GroupProfile.objects.move(self.team_a, self.company_b, "last-child")
        )
        self.assertEqual(self.tree_state(), before)
        self.assertEqual(self.team_a.path, old_path)
        self.assertEqual(
            self.memberships(self.user), {self.company_a.group_id, self.nested_a.group_id}
        )

    def test_promoting_department_to_company_rolls_back_sibling_renumbering(self):
        self.user.groups.add(self.company_a.group, self.team_a.group)
        before = self.tree_state()
        self.assert_company_conflict(
            lambda: GroupProfile.objects.move(self.team_a, self.company_a, "first-sibling")
        )
        self.assertEqual(self.tree_state(), before)
        self.assertEqual(
            self.memberships(self.user), {self.company_a.group_id, self.team_a.group_id}
        )

    def test_moving_an_external_subtree_into_another_company_checks_its_members(self):
        external_team = self.child(self.unrelated)
        self.user.groups.add(self.company_a.group, external_team.group)
        before = self.tree_state()
        self.assert_company_conflict(
            lambda: GroupProfile.objects.move(external_team, self.company_b, "last-child")
        )
        self.assertEqual(self.tree_state(), before)
        self.assertEqual(
            self.memberships(self.user), {self.company_a.group_id, external_team.group_id}
        )

    def test_move_within_company_preserves_multiple_department_memberships(self):
        self.user.groups.add(self.company_a.group, self.team_a.group, self.nested_a.group)
        GroupProfile.objects.move(self.team_a, self.other_team_a, "last-child")
        self.assertEqual(GroupProfile.objects.get_parent(self.team_a), self.other_team_a)
        self.assertEqual(
            self.memberships(self.user),
            {self.company_a.group_id, self.team_a.group_id, self.nested_a.group_id},
        )

    def test_company_reordering_uses_stable_company_identity_not_old_paths(self):
        self.user.groups.add(self.company_a.group, self.team_a.group)
        other_user = UserFactory()
        other_user.groups.add(self.company_b.group, self.team_b.group)
        old_a_path = self.company_a.path
        GroupProfile.objects.move(self.company_b, self.company_a, "left")
        self.company_a.refresh_from_db()
        self.assertNotEqual(self.company_a.path, old_a_path)
        self.assertEqual(GroupProfile.objects.get_parent(self.company_a), self.root)
        self.assertEqual(GroupProfile.objects.get_parent(self.company_b), self.root)
        self.assertEqual(
            self.memberships(self.user), {self.company_a.group_id, self.team_a.group_id}
        )
        self.assertEqual(
            self.memberships(other_user), {self.company_b.group_id, self.team_b.group_id}
        )

    def test_legacy_conflict_does_not_prevent_ancestry_preserving_reorder(self):
        self.add_legacy_conflict(self.user)
        GroupProfile.objects.move(self.company_b, self.company_a, "left")
        self.assertEqual(GroupProfile.objects.get_parent(self.company_b), self.root)
        self.assertEqual(
            self.memberships(self.user), {self.company_a.group_id, self.company_b.group_id}
        )

    def test_move_checks_other_profiles_of_the_same_group(self):
        self.child(self.other_team_a, group=self.team_a.group)
        self.user.groups.add(self.team_a.group)
        before = self.tree_state()
        self.assert_company_conflict(
            lambda: GroupProfile.objects.move(self.team_a, self.company_b, "last-child")
        )
        self.assertEqual(self.tree_state(), before)
        self.assertEqual(self.memberships(self.user), {self.team_a.group_id})


@override_settings(ENTERPRISE_GROUP_SLUG="membership-concurrency-root", ES_LIVE_INDEXING=False)
class EnterpriseMembershipConcurrencyTests(MembershipFixtures, TransactionTestCase):
    def test_competing_company_additions_have_one_winner(self):
        barrier = Barrier(2, timeout=10)
        lock_users = membership._lock_users

        def synchronize_users(user_ids, using):
            barrier.wait()
            lock_users(user_ids, using)

        def add(group_id):
            try:
                user = User.all_users.get(pk=self.user.pk)
                user.groups.add(group_id)
                return group_id
            except ValidationError as error:
                return error.code
            finally:
                connections.close_all()

        connections.close_all()
        with (
            patch("kitsune.groups.membership._lock_users", synchronize_users),
            ThreadPoolExecutor(max_workers=2) as pool,
        ):
            results = list(pool.map(add, (self.team_a.group_id, self.team_b.group_id)))
        self.assertEqual(results.count("company_conflict"), 1)
        winner = next(result for result in results if result != "company_conflict")
        self.assertEqual(self.memberships(self.user), {winner})

    def test_first_member_addition_cannot_race_an_empty_department_move(self):
        self.user.groups.add(self.company_a.group)
        member_locked = Event()
        move_requested = Event()
        lock_users = membership._lock_users
        hierarchy_gate = membership.lock_enterprise_hierarchy
        before = self.tree_state()

        def pause_member(user_ids, using):
            lock_users(user_ids, using)
            if not move_requested.is_set():
                member_locked.set()
                if not move_requested.wait(timeout=10):
                    raise AssertionError("The concurrent hierarchy move did not start")

        @contextmanager
        def observe_gate(*, using="default", exclusive=False):
            if exclusive:
                move_requested.set()
            with hierarchy_gate(using=using, exclusive=exclusive):
                yield

        def add():
            try:
                User.all_users.get(pk=self.user.pk).groups.add(self.team_a.group_id)
                return "added"
            finally:
                connections.close_all()

        def move():
            try:
                if not member_locked.wait(timeout=10):
                    raise AssertionError("The concurrent membership addition did not start")
                GroupProfile.objects.move(self.team_a, self.company_b, "last-child")
                return "moved"
            except ValidationError as error:
                return error.code
            finally:
                connections.close_all()

        connections.close_all()
        with (
            patch("kitsune.groups.membership._lock_users", pause_member),
            patch("kitsune.groups.membership.lock_enterprise_hierarchy", observe_gate),
            ThreadPoolExecutor(max_workers=2) as pool,
        ):
            addition = pool.submit(add)
            movement = pool.submit(move)
            self.assertEqual(addition.result(timeout=20), "added")
            self.assertEqual(movement.result(timeout=20), "company_conflict")
        self.assertEqual(self.tree_state(), before)
        self.assertEqual(
            self.memberships(self.user), {self.company_a.group_id, self.team_a.group_id}
        )

    def test_membership_addition_observes_a_move_that_acquires_the_gate_first(self):
        self.user.groups.add(self.company_a.group)
        move_locked = Event()
        member_requested = Event()
        hierarchy_gate = membership.lock_enterprise_hierarchy

        @contextmanager
        def pause_move(*, using="default", exclusive=False):
            if not exclusive:
                member_requested.set()
            with hierarchy_gate(using=using, exclusive=exclusive):
                if exclusive:
                    move_locked.set()
                    if not member_requested.wait(timeout=10):
                        raise AssertionError("The concurrent membership addition did not start")
                yield

        def move():
            try:
                GroupProfile.objects.move(self.team_a, self.company_b, "last-child")
                return "moved"
            finally:
                connections.close_all()

        def add():
            try:
                if not move_locked.wait(timeout=10):
                    raise AssertionError("The concurrent hierarchy move did not start")
                User.all_users.get(pk=self.user.pk).groups.add(self.team_a.group_id)
                return "added"
            except ValidationError as error:
                return error.code
            finally:
                connections.close_all()

        connections.close_all()
        with (
            patch("kitsune.groups.membership.lock_enterprise_hierarchy", pause_move),
            ThreadPoolExecutor(max_workers=2) as pool,
        ):
            movement = pool.submit(move)
            addition = pool.submit(add)
            self.assertEqual(movement.result(timeout=20), "moved")
            self.assertEqual(addition.result(timeout=20), "company_conflict")
        self.team_a.refresh_from_db()
        self.assertEqual(GroupProfile.objects.get_parent(self.team_a), self.company_b)
        self.assertEqual(self.memberships(self.user), {self.company_a.group_id})
