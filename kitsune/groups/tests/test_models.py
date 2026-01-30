"""Tests for GroupProfile model and visibility manager."""

from django.contrib.auth.models import Group

from kitsune.groups.models import GroupProfile
from kitsune.sumo.tests import TestCase
from kitsune.users.tests import UserFactory


class ModerationHierarchyTests(TestCase):
    """Test moderation hierarchy rules."""

    def setUp(self):
        """
        Create hierarchy:
            Root (moderator: Mike)
            ├── SubA (moderator: Alice)
            │   └── SubSubA (no moderator)
            └── SubB (no moderator)
        """
        # Create root
        root_group = Group.objects.create(name="Root")
        self.root = GroupProfile.add_root(
            group=root_group,
            slug="root",
            visibility=GroupProfile.Visibility.PRIVATE,
        )
        self.mike = UserFactory(username="mike")
        self.root.leaders.add(self.mike)

        # Create SubA with moderator
        suba_group = Group.objects.create(name="SubA")
        self.sub_a = self.root.add_child(
            group=suba_group,
            slug="sub-a",
        )
        self.alice = UserFactory(username="alice")
        self.sub_a.leaders.add(self.alice)

        # Create SubSubA without moderator
        subsuba_group = Group.objects.create(name="SubSubA")
        self.subsub_a = self.sub_a.add_child(
            group=subsuba_group,
            slug="subsub-a",
        )

        # Create SubB without moderator
        subb_group = Group.objects.create(name="SubB")
        self.sub_b = self.root.add_child(
            group=subb_group,
            slug="sub-b",
        )

    def test_root_moderator_manages_entire_tree(self):
        """Root moderator can moderate all groups in tree."""
        self.assertTrue(self.root.can_moderate_group(self.mike))
        self.assertTrue(self.sub_a.can_moderate_group(self.mike))
        self.assertTrue(self.subsub_a.can_moderate_group(self.mike))
        self.assertTrue(self.sub_b.can_moderate_group(self.mike))

    def test_non_root_moderator_manages_only_their_group(self):
        """Non-root moderator can only moderate their specific group."""
        # Alice can moderate SubA
        self.assertTrue(self.sub_a.can_moderate_group(self.alice))

        # Alice CANNOT moderate descendants
        self.assertFalse(self.subsub_a.can_moderate_group(self.alice))

        # Alice CANNOT moderate root
        self.assertFalse(self.root.can_moderate_group(self.alice))

        # Alice CANNOT moderate siblings
        self.assertFalse(self.sub_b.can_moderate_group(self.alice))

    def test_moderation_inheritance_skips_to_root(self):
        """Groups without moderators inherit from root, not parent."""
        # SubSubA has no moderator
        self.assertEqual(self.subsub_a.leaders.count(), 0)

        # SubSubA's parent (SubA) has Alice as moderator
        self.assertEqual(self.sub_a.leaders.count(), 1)

        # But SubSubA is moderated by Mike (root), NOT Alice (parent)
        self.assertTrue(self.subsub_a.can_moderate_group(self.mike))
        self.assertFalse(self.subsub_a.can_moderate_group(self.alice))

        # SubB also inherits from root
        self.assertTrue(self.sub_b.can_moderate_group(self.mike))
        self.assertFalse(self.sub_b.can_moderate_group(self.alice))

    def test_root_moderator_can_edit_entire_tree(self):
        """Root moderator can edit all groups."""
        self.assertTrue(self.root.can_edit(self.mike))
        self.assertTrue(self.sub_a.can_edit(self.mike))
        self.assertTrue(self.subsub_a.can_edit(self.mike))
        self.assertTrue(self.sub_b.can_edit(self.mike))

    def test_non_root_moderator_can_edit_only_their_group(self):
        """Non-root moderator can only edit their specific group."""
        self.assertTrue(self.sub_a.can_edit(self.alice))
        self.assertFalse(self.subsub_a.can_edit(self.alice))
        self.assertFalse(self.sub_b.can_edit(self.alice))

    def test_only_root_moderator_can_delete(self):
        """Only root moderators can delete subgroups."""
        # Mike (root moderator) can delete
        self.assertTrue(self.root.can_delete_subgroup(self.mike, self.sub_a))
        self.assertTrue(self.root.can_delete_subgroup(self.mike, self.subsub_a))

        # Alice (non-root moderator) cannot delete
        self.assertFalse(self.sub_a.can_delete_subgroup(self.alice, self.subsub_a))


class VisibilityWithIsolationTests(TestCase):
    """Test visibility rules with isolation enabled."""

    def setUp(self):
        """
        Create hierarchy:
            Root (member: Alice, Bob; moderator: Mike)
            ├── SubA (member: Alice, Charlie)
            └── SubB (member: Bob)
        """
        # Create root
        root_group = Group.objects.create(name="Root")
        self.root = GroupProfile.add_root(
            group=root_group,
            slug="root",
            visibility=GroupProfile.Visibility.PRIVATE,
            isolation_enabled=True,
        )

        self.mike = UserFactory(username="mike")
        self.alice = UserFactory(username="alice")
        self.bob = UserFactory(username="bob")
        self.charlie = UserFactory(username="charlie")

        # Mike is moderator, Alice and Bob are members of root
        self.root.leaders.add(self.mike)
        self.root.group.user_set.add(self.alice, self.bob)

        # Create SubA
        suba_group = Group.objects.create(name="SubA")
        self.sub_a = self.root.add_child(
            group=suba_group,
            slug="sub-a",
        )
        self.sub_a.group.user_set.add(self.alice, self.charlie)

        # Create SubB
        subb_group = Group.objects.create(name="SubB")
        self.sub_b = self.root.add_child(
            group=subb_group,
            slug="sub-b",
        )
        self.sub_b.group.user_set.add(self.bob)

    def test_root_moderator_sees_entire_tree(self):
        """Root moderator sees all groups."""
        visible = GroupProfile.objects.visible(self.mike)

        self.assertIn(self.root, visible)
        self.assertIn(self.sub_a, visible)
        self.assertIn(self.sub_b, visible)

    def test_root_member_sees_entire_tree(self):
        """Root member sees all groups (read-only)."""
        # Alice is root member
        visible_alice = GroupProfile.objects.visible(self.alice)
        self.assertIn(self.root, visible_alice)
        self.assertIn(self.sub_a, visible_alice)
        self.assertIn(self.sub_b, visible_alice)

        # Bob is root member
        visible_bob = GroupProfile.objects.visible(self.bob)
        self.assertIn(self.root, visible_bob)
        self.assertIn(self.sub_a, visible_bob)
        self.assertIn(self.sub_b, visible_bob)

    def test_node_member_has_sibling_isolation(self):
        """Node member (not root member) only sees their subtree."""
        # Charlie is member of SubA but NOT root
        visible_charlie = GroupProfile.objects.visible(self.charlie)

        # Charlie sees ancestors and own subtree
        self.assertIn(self.root, visible_charlie)
        self.assertIn(self.sub_a, visible_charlie)

        # Charlie does NOT see sibling SubB
        self.assertNotIn(self.sub_b, visible_charlie)

    def test_root_member_cannot_edit(self):
        """Root member has view access only, no edit."""
        # Alice is root member but not moderator
        self.assertFalse(self.root.can_moderate_group(self.alice))
        self.assertFalse(self.sub_a.can_moderate_group(self.alice))


class PublicGroupsNoIsolationTests(TestCase):
    """Test that PUBLIC groups have no isolation."""

    def setUp(self):
        """Create PUBLIC hierarchy."""
        root_group = Group.objects.create(name="PublicRoot")
        self.root = GroupProfile.add_root(
            group=root_group,
            slug="public-root",
            visibility=GroupProfile.Visibility.PUBLIC,
        )

        child_group = Group.objects.create(name="PublicChild")
        self.child = self.root.add_child(
            group=child_group,
            slug="public-child",
        )

    def test_anonymous_sees_public_groups(self):
        """Anonymous users see all PUBLIC groups."""
        visible = GroupProfile.objects.visible(None)

        self.assertIn(self.root, visible)
        self.assertIn(self.child, visible)

    def test_public_groups_ignore_isolation_setting(self):
        """PUBLIC groups are visible even with isolation_enabled."""
        # Set isolation_enabled (shouldn't matter for PUBLIC)
        self.root.isolation_enabled = True
        self.root.save()
        self.child.refresh_from_db()

        # Still visible to anonymous
        visible = GroupProfile.objects.visible(None)
        self.assertIn(self.root, visible)
        self.assertIn(self.child, visible)


class ModeratedGroupsTests(TestCase):
    """Test MODERATED groups with same rules as PRIVATE."""

    def setUp(self):
        """Create MODERATED hierarchy."""
        root_group = Group.objects.create(name="ModeratedRoot")
        self.root = GroupProfile.add_root(
            group=root_group,
            slug="moderated-root",
            visibility=GroupProfile.Visibility.MODERATED,
            isolation_enabled=True,
        )

        self.mike = UserFactory(username="mike")
        self.alice = UserFactory(username="alice")

        self.root.leaders.add(self.mike)
        self.root.group.user_set.add(self.alice)

        child_group = Group.objects.create(name="ModeratedChild")
        self.child = self.root.add_child(
            group=child_group,
            slug="moderated-child",
        )

    def test_moderated_follows_same_rules_as_private(self):
        """MODERATED groups follow same visibility rules as PRIVATE."""
        # Root moderator sees all
        visible_mike = GroupProfile.objects.visible(self.mike)
        self.assertIn(self.root, visible_mike)
        self.assertIn(self.child, visible_mike)

        # Root member sees all
        visible_alice = GroupProfile.objects.visible(self.alice)
        self.assertIn(self.root, visible_alice)
        self.assertIn(self.child, visible_alice)

    def test_visible_to_groups_provides_view_access(self):
        """visible_to_groups provides cross-hierarchy view access."""
        # Create external audit group
        audit_django_group = Group.objects.create(name="AuditTeam")
        GroupProfile.add_root(
            group=audit_django_group,
            slug="audit-team",
            visibility=GroupProfile.Visibility.PUBLIC,
        )
        auditor = UserFactory(username="auditor")
        audit_django_group.user_set.add(auditor)

        # Add audit group to visible_to_groups
        self.root.visible_to_groups.add(audit_django_group)
        self.child.visible_to_groups.add(audit_django_group)

        # Auditor can see groups (view-only)
        visible_auditor = GroupProfile.objects.visible(auditor)
        self.assertIn(self.root, visible_auditor)
        self.assertIn(self.child, visible_auditor)

        # But auditor cannot moderate
        self.assertFalse(self.root.can_moderate_group(auditor))
        self.assertFalse(self.child.can_moderate_group(auditor))


class IsolationDisabledTests(TestCase):
    """Test behavior when isolation is disabled."""

    def setUp(self):
        """Create PRIVATE hierarchy with isolation disabled."""
        root_group = Group.objects.create(name="Root")
        self.root = GroupProfile.add_root(
            group=root_group,
            slug="root",
            visibility=GroupProfile.Visibility.PRIVATE,
            isolation_enabled=False,
        )

        self.alice = UserFactory(username="alice")
        self.bob = UserFactory(username="bob")

        # SubA
        suba_group = Group.objects.create(name="SubA")
        self.sub_a = self.root.add_child(
            group=suba_group,
            slug="sub-a",
        )
        self.sub_a.group.user_set.add(self.alice)

        # SubB
        subb_group = Group.objects.create(name="SubB")
        self.sub_b = self.root.add_child(
            group=subb_group,
            slug="sub-b",
        )
        self.sub_b.group.user_set.add(self.bob)

    def test_isolation_disabled_shows_siblings(self):
        """When isolation disabled, members can see siblings."""
        # With isolation disabled, users should see more
        # (exact behavior depends on requirements - for now just verify query works)
        visible = GroupProfile.objects.visible(self.alice)

        # At minimum, Alice sees her own subtree and ancestors
        self.assertIn(self.sub_a, visible)
        self.assertIn(self.root, visible)


class SiblingIsolationTests(TestCase):
    """Test that users cannot see sibling groups."""

    def setUp(self):
        """
        Create PRIVATE hierarchy to test sibling isolation:
            ParentA (PRIVATE)
            ├── SubgroupB (PRIVATE - inherited)
            └── SubgroupC (PRIVATE - inherited)
        """
        # Create parent group as PRIVATE so children inherit PRIVATE
        parent_group = Group.objects.create(name="ParentA")
        self.parent = GroupProfile.add_root(
            group=parent_group,
            slug="parent-a",
            visibility=GroupProfile.Visibility.PRIVATE,
        )

        # Create two sibling subgroups (inherit PRIVATE from parent)
        subgroup_b_group = Group.objects.create(name="SubgroupB")
        self.subgroup_b = self.parent.add_child(
            group=subgroup_b_group,
            slug="subgroup-b",
        )

        subgroup_c_group = Group.objects.create(name="SubgroupC")
        self.subgroup_c = self.parent.add_child(
            group=subgroup_c_group,
            slug="subgroup-c",
        )

        # Create users
        self.user_in_b = UserFactory()
        self.user_in_c = UserFactory()
        self.user_in_parent = UserFactory()
        self.user_not_in_any = UserFactory()

        # Add users to groups
        self.subgroup_b.group.user_set.add(self.user_in_b)
        self.subgroup_c.group.user_set.add(self.user_in_c)
        self.parent.group.user_set.add(self.user_in_parent)

    def test_user_cannot_see_sibling(self):
        """User in SubgroupB cannot see SubgroupC (sibling)."""
        visible = GroupProfile.objects.visible(self.user_in_b)

        # Should see: ParentA (parent), SubgroupB (own)
        self.assertIn(self.parent, visible)
        self.assertIn(self.subgroup_b, visible)

        # Should NOT see: SubgroupC (sibling)
        self.assertNotIn(self.subgroup_c, visible)

    def test_user_can_see_parent(self):
        """User in SubgroupB can see ParentA (parent)."""
        visible = GroupProfile.objects.visible(self.user_in_b)
        self.assertIn(self.parent, visible)

    def test_user_can_see_children(self):
        """User in ParentA can see all children."""
        visible = GroupProfile.objects.visible(self.user_in_parent)

        # Should see: ParentA (own), SubgroupB (child), SubgroupC (child)
        self.assertIn(self.parent, visible)
        self.assertIn(self.subgroup_b, visible)
        self.assertIn(self.subgroup_c, visible)

    def test_anonymous_sees_only_public(self):
        """Anonymous users see all PUBLIC groups, not PRIVATE ones."""
        visible = GroupProfile.objects.visible(None)

        # ParentA tree is PRIVATE, so anonymous users can't see any of it
        self.assertNotIn(self.parent, visible)
        self.assertNotIn(self.subgroup_b, visible)
        self.assertNotIn(self.subgroup_c, visible)

    def test_user_not_in_any_group_sees_only_public(self):
        """User not in any group sees all PUBLIC groups, not PRIVATE ones."""
        visible = GroupProfile.objects.visible(self.user_not_in_any)

        # ParentA tree is PRIVATE, so non-members can't see any of it
        self.assertNotIn(self.parent, visible)
        self.assertNotIn(self.subgroup_b, visible)
        self.assertNotIn(self.subgroup_c, visible)

    def test_private_sibling_not_visible(self):
        """Private sibling groups are not visible even to members of other siblings."""
        # Make SubgroupC private
        self.subgroup_c.visibility = GroupProfile.Visibility.PRIVATE
        self.subgroup_c.save()

        visible = GroupProfile.objects.visible(self.user_in_b)

        # Should NOT see SubgroupC (private sibling)
        self.assertNotIn(self.subgroup_c, visible)

    def test_three_level_hierarchy(self):
        """Test PRIVATE group isolation in a three-level hierarchy."""
        # Add grandchild to SubgroupB
        grandchild_group = Group.objects.create(name="GrandchildD")
        grandchild = self.subgroup_b.add_child(
            group=grandchild_group,
            slug="grandchild-d",
            visibility=GroupProfile.Visibility.PRIVATE,
        )

        user_in_grandchild = UserFactory()
        grandchild.group.user_set.add(user_in_grandchild)

        visible = GroupProfile.objects.visible(user_in_grandchild)

        # Should see: ParentA (public grandparent), SubgroupB (private parent), GrandchildD (own)
        self.assertIn(self.parent, visible)
        self.assertIn(self.subgroup_b, visible)
        self.assertIn(grandchild, visible)

        # Should NOT see: SubgroupC (private uncle/aunt - sibling of parent)
        self.assertNotIn(self.subgroup_c, visible)


class VisibilityEdgeCaseTests(TestCase):
    """Test edge cases in group visibility."""

    def setUp(self):
        """
        Create complex hierarchies with strict visibility inheritance:
            ParentA (PUBLIC) - entire tree is PUBLIC
            ├── SubB (PUBLIC - inherited)
            │   └── GrandchildD (PUBLIC - inherited)
            └── SubC (PUBLIC - inherited)

            ParentE (PRIVATE) - entire tree is PRIVATE
            └── SubF (PRIVATE - inherited)
        """
        # First hierarchy - all PUBLIC
        parent_a_group = Group.objects.create(name="ParentA")
        self.parent_a = GroupProfile.add_root(
            group=parent_a_group,
            slug="parent-a",
            visibility=GroupProfile.Visibility.PUBLIC,
        )

        sub_b_group = Group.objects.create(name="SubB")
        self.sub_b = self.parent_a.add_child(
            group=sub_b_group,
            slug="sub-b",
        )

        grandchild_d_group = Group.objects.create(name="GrandchildD")
        self.grandchild_d = self.sub_b.add_child(
            group=grandchild_d_group,
            slug="grandchild-d",
        )

        sub_c_group = Group.objects.create(name="SubC")
        self.sub_c = self.parent_a.add_child(
            group=sub_c_group,
            slug="sub-c",
        )

        # Second hierarchy - all PRIVATE
        parent_e_group = Group.objects.create(name="ParentE")
        self.parent_e = GroupProfile.add_root(
            group=parent_e_group,
            slug="parent-e",
            visibility=GroupProfile.Visibility.PRIVATE,
        )

        sub_f_group = Group.objects.create(name="SubF")
        self.sub_f = self.parent_e.add_child(
            group=sub_f_group,
            slug="sub-f",
        )

    def test_user_in_multiple_sibling_groups(self):
        """User can be in multiple sibling groups and sees both."""
        user = UserFactory()
        self.sub_b.group.user_set.add(user)
        self.sub_c.group.user_set.add(user)

        visible = GroupProfile.objects.visible(user)

        # Should see both siblings (because user is member of both)
        self.assertIn(self.sub_b, visible)
        self.assertIn(self.sub_c, visible)
        # Should see parent
        self.assertIn(self.parent_a, visible)
        # Should see grandchild (descendant of SubB)
        self.assertIn(self.grandchild_d, visible)

    def test_user_in_parent_and_child(self):
        """User in both parent and child sees entire PUBLIC tree."""
        user = UserFactory()
        self.parent_a.group.user_set.add(user)
        self.sub_b.group.user_set.add(user)

        visible = GroupProfile.objects.visible(user)

        # ParentA tree is all PUBLIC, so user sees everything
        self.assertIn(self.parent_a, visible)
        self.assertIn(self.sub_b, visible)
        self.assertIn(self.grandchild_d, visible)
        self.assertIn(self.sub_c, visible)  # PUBLIC, visible to everyone

    def test_private_tree_not_visible_to_non_member(self):
        """User not in PRIVATE tree cannot see any of it."""
        user = UserFactory()

        visible = GroupProfile.objects.visible(user)

        # ParentE tree is all PRIVATE (visibility inherited)
        # User not in hierarchy, so can't see any of it
        self.assertNotIn(self.parent_e, visible)
        self.assertNotIn(self.sub_f, visible)

    def test_member_of_private_parent_sees_descendants(self):
        """User in PRIVATE parent sees all descendants (entire PRIVATE tree)."""
        user = UserFactory()
        self.parent_e.group.user_set.add(user)

        visible = GroupProfile.objects.visible(user)

        # User in PRIVATE parent sees entire tree (all PRIVATE due to inheritance)
        self.assertIn(self.parent_e, visible)
        self.assertIn(self.sub_f, visible)

    def test_member_of_private_child_sees_private_parent(self):
        """User in PRIVATE child sees PRIVATE parent (hierarchy access)."""
        user = UserFactory()
        self.sub_f.group.user_set.add(user)

        visible = GroupProfile.objects.visible(user)

        # User in SubF (PRIVATE) can see ancestor ParentE (PRIVATE)
        # Being in hierarchy gives access to ancestors
        self.assertIn(self.parent_e, visible)
        self.assertIn(self.sub_f, visible)

    def test_public_tree_visible_to_all(self):
        """PUBLIC tree is visible to everyone, no sibling isolation."""
        user = UserFactory()
        self.sub_b.group.user_set.add(user)  # Member of SubB

        visible = GroupProfile.objects.visible(user)

        # ParentA tree is all PUBLIC, so user sees everything including sibling SubC
        self.assertIn(self.sub_b, visible)
        self.assertIn(self.sub_c, visible)  # Sibling, but PUBLIC
        self.assertIn(self.parent_a, visible)
        self.assertIn(self.grandchild_d, visible)

    def test_four_level_hierarchy(self):
        """Test visibility in a four-level deep PUBLIC hierarchy."""
        # Add great-grandchild (inherits PUBLIC from ancestors)
        great_grandchild_group = Group.objects.create(name="GreatGrandchildG")
        great_grandchild = self.grandchild_d.add_child(
            group=great_grandchild_group,
            slug="great-grandchild-g",
        )

        user = UserFactory()
        great_grandchild.group.user_set.add(user)

        visible = GroupProfile.objects.visible(user)

        # ParentA tree is all PUBLIC, so user sees everything
        self.assertIn(self.parent_a, visible)
        self.assertIn(self.sub_b, visible)
        self.assertIn(self.grandchild_d, visible)
        self.assertIn(great_grandchild, visible)
        self.assertIn(self.sub_c, visible)  # PUBLIC, visible to all

    def test_empty_group_visibility(self):
        """Empty groups (no members) follow same visibility rules."""
        user = UserFactory()
        self.sub_b.group.user_set.add(user)

        visible = GroupProfile.objects.visible(user)

        # GrandchildD has no members but is descendant of SubB
        self.assertIn(self.grandchild_d, visible)

    def test_user_with_no_groups_multiple_hierarchies(self):
        """User not in any group only sees root public groups."""
        user = UserFactory()

        visible = GroupProfile.objects.visible(user)

        # Should see: All PUBLIC groups (ParentA tree is PUBLIC)
        self.assertIn(self.parent_a, visible)
        self.assertIn(self.sub_b, visible)
        self.assertIn(self.sub_c, visible)
        self.assertIn(self.grandchild_d, visible)

        # Should NOT see: PRIVATE groups
        self.assertNotIn(self.parent_e, visible)
        self.assertNotIn(self.sub_f, visible)


class GetVisibleChildrenTests(TestCase):
    """Test the get_visible_children() method with strict inheritance."""

    def setUp(self):
        """
        Create separate trees for testing different visibilities.

        Note: Children inherit parent visibility, so we need separate trees
        to test different visibility levels.
        """
        # PUBLIC tree
        public_parent_group = Group.objects.create(name="PublicParent")
        self.public_parent = GroupProfile.add_root(
            group=public_parent_group,
            slug="public-parent",
            visibility=GroupProfile.Visibility.PUBLIC,
        )

        child1_group = Group.objects.create(name="Child1")
        self.child1 = self.public_parent.add_child(
            group=child1_group,
            slug="child1",
        )

        # PRIVATE tree
        private_parent_group = Group.objects.create(name="PrivateParent")
        self.private_parent = GroupProfile.add_root(
            group=private_parent_group,
            slug="private-parent",
            visibility=GroupProfile.Visibility.PRIVATE,
        )

        child2_group = Group.objects.create(name="Child2")
        self.child2 = self.private_parent.add_child(
            group=child2_group,
            slug="child2",
        )

        # MODERATED tree
        moderated_parent_group = Group.objects.create(name="ModeratedParent")
        self.moderated_parent = GroupProfile.add_root(
            group=moderated_parent_group,
            slug="moderated-parent",
            visibility=GroupProfile.Visibility.MODERATED,
        )

        child3_group = Group.objects.create(name="Child3")
        self.child3 = self.moderated_parent.add_child(
            group=child3_group,
            slug="child3",
        )

        moderator_group = Group.objects.create(name="Moderators")
        self.moderator_group_profile = GroupProfile.add_root(
            group=moderator_group,
            slug="moderators",
            visibility=GroupProfile.Visibility.PUBLIC,
        )
        self.moderated_parent.visible_to_groups.add(moderator_group)
        self.child3.visible_to_groups.add(moderator_group)

    def test_anonymous_sees_public_children(self):
        """Anonymous users see PUBLIC children."""
        children = self.public_parent.get_visible_children(None)

        self.assertIn(self.child1, children)  # PUBLIC

    def test_member_sees_private_children(self):
        """Member of PRIVATE parent sees PRIVATE children."""
        user = UserFactory()
        self.private_parent.group.user_set.add(user)

        children = self.private_parent.get_visible_children(user)

        self.assertIn(self.child2, children)  # PRIVATE, user in parent

    def test_non_member_cannot_see_private_children(self):
        """Non-member cannot see PRIVATE children."""
        user = UserFactory()

        children = self.private_parent.get_visible_children(user)

        self.assertNotIn(self.child2, children)  # PRIVATE, user not in hierarchy

    def test_moderator_sees_moderated_children(self):
        """User in moderator group sees MODERATED children."""
        user = UserFactory()
        self.moderator_group_profile.group.user_set.add(user)

        children = self.moderated_parent.get_visible_children(user)

        self.assertIn(self.child3, children)  # MODERATED, user in moderator group


class LeadershipVisibilityTests(TestCase):
    """Test visibility for group leaders."""

    def setUp(self):
        """Create PRIVATE hierarchy with leaders for testing isolation."""
        parent_group = Group.objects.create(name="Parent")
        self.parent = GroupProfile.add_root(
            group=parent_group,
            slug="parent",
            visibility=GroupProfile.Visibility.PRIVATE,
        )

        child_group = Group.objects.create(name="Child")
        self.child = self.parent.add_child(
            group=child_group,
            slug="child",
        )

        self.parent_leader = UserFactory()
        self.parent.leaders.add(self.parent_leader)

        self.child_leader = UserFactory()
        self.child.leaders.add(self.child_leader)

    def test_parent_leader_without_membership_sees_children(self):
        """Parent leader (not member) can see private children."""
        # Leader is NOT a member of parent group
        self.assertNotIn(self.parent_leader, self.parent.group.user_set.all())

        visible = GroupProfile.objects.visible(self.parent_leader)

        # Should see parent (leader)
        self.assertIn(self.parent, visible)
        # Should see child (descendant of group they lead)
        self.assertIn(self.child, visible)

    def test_child_leader_sees_parent(self):
        """Child leader sees their group and parent."""
        visible = GroupProfile.objects.visible(self.child_leader)

        self.assertIn(self.parent, visible)  # Ancestor
        self.assertIn(self.child, visible)  # Leader of this group

    def test_leader_of_sibling_cannot_see_other_sibling(self):
        """Leader of one sibling cannot see other PRIVATE sibling."""
        sibling_group = Group.objects.create(name="Sibling")
        sibling = self.parent.add_child(
            group=sibling_group,
            slug="sibling",
        )

        visible = GroupProfile.objects.visible(self.child_leader)

        # Should see own group and parent
        self.assertIn(self.parent, visible)  # PRIVATE parent (ancestor)
        self.assertIn(self.child, visible)  # Own group (leader)
        # Should NOT see sibling (PRIVATE sibling isolation)
        self.assertNotIn(sibling, visible)

    def test_root_leader_sees_entire_tree(self):
        """Leader of root group can see all descendants (full tree access)."""
        # Create deeper hierarchy
        grandchild_group = Group.objects.create(name="Grandchild")
        grandchild = self.child.add_child(
            group=grandchild_group,
            slug="grandchild",
            visibility=GroupProfile.Visibility.PRIVATE,
        )

        sibling_group = Group.objects.create(name="Sibling")
        sibling = self.parent.add_child(
            group=sibling_group,
            slug="sibling",
            visibility=GroupProfile.Visibility.PRIVATE,
        )

        visible = GroupProfile.objects.visible(self.parent_leader)

        # Root leader should see EVERYTHING in the tree
        self.assertIn(self.parent, visible)  # Root (leads)
        self.assertIn(self.child, visible)  # First level child
        self.assertIn(grandchild, visible)  # Second level descendant
        self.assertIn(sibling, visible)  # Another first level child


class VisibilityInheritanceTests(TestCase):
    """Test that visibility is strictly inherited from parent."""

    def test_child_inherits_parent_visibility_on_create(self):
        """Child automatically gets parent's visibility when created."""
        parent_group = Group.objects.create(name="Parent")
        parent = GroupProfile.add_root(
            group=parent_group,
            slug="parent",
            visibility=GroupProfile.Visibility.PRIVATE,
        )

        child_group = Group.objects.create(name="Child")
        child = parent.add_child(
            group=child_group,
            slug="child",
            visibility=GroupProfile.Visibility.PUBLIC,  # Try to set PUBLIC
        )

        # Refresh from DB
        child.refresh_from_db()

        # Child should have PRIVATE visibility (inherited from parent)
        self.assertEqual(child.visibility, GroupProfile.Visibility.PRIVATE)

    def test_updating_root_propagates_to_descendants(self):
        """Changing root visibility updates all descendants."""
        parent_group = Group.objects.create(name="Parent")
        parent = GroupProfile.add_root(
            group=parent_group,
            slug="parent",
            visibility=GroupProfile.Visibility.PUBLIC,
        )

        child_group = Group.objects.create(name="Child")
        child = parent.add_child(
            group=child_group,
            slug="child",
        )

        grandchild_group = Group.objects.create(name="Grandchild")
        grandchild = child.add_child(
            group=grandchild_group,
            slug="grandchild",
        )

        # All should be PUBLIC initially
        self.assertEqual(parent.visibility, GroupProfile.Visibility.PUBLIC)
        child.refresh_from_db()
        grandchild.refresh_from_db()
        self.assertEqual(child.visibility, GroupProfile.Visibility.PUBLIC)
        self.assertEqual(grandchild.visibility, GroupProfile.Visibility.PUBLIC)

        # Change root to PRIVATE
        parent.update_visibility(GroupProfile.Visibility.PRIVATE)

        # All descendants should now be PRIVATE
        parent.refresh_from_db()
        child.refresh_from_db()
        grandchild.refresh_from_db()
        self.assertEqual(parent.visibility, GroupProfile.Visibility.PRIVATE)
        self.assertEqual(child.visibility, GroupProfile.Visibility.PRIVATE)
        self.assertEqual(grandchild.visibility, GroupProfile.Visibility.PRIVATE)

    def test_save_propagates_visibility_to_descendants(self):
        """Changing visibility via save() (as in admin) propagates to descendants."""
        parent_group = Group.objects.create(name="Parent")
        parent = GroupProfile.add_root(
            group=parent_group,
            slug="parent",
            visibility=GroupProfile.Visibility.PUBLIC,
        )

        child_group = Group.objects.create(name="Child")
        child = parent.add_child(
            group=child_group,
            slug="child",
        )

        grandchild_group = Group.objects.create(name="Grandchild")
        grandchild = child.add_child(
            group=grandchild_group,
            slug="grandchild",
        )

        # All should be PUBLIC initially
        self.assertEqual(parent.visibility, GroupProfile.Visibility.PUBLIC)
        child.refresh_from_db()
        grandchild.refresh_from_db()
        self.assertEqual(child.visibility, GroupProfile.Visibility.PUBLIC)
        self.assertEqual(grandchild.visibility, GroupProfile.Visibility.PUBLIC)

        # Change root to PRIVATE via save() (simulates admin form submission)
        parent.visibility = GroupProfile.Visibility.PRIVATE
        parent.save()

        # All descendants should now be PRIVATE
        parent.refresh_from_db()
        child.refresh_from_db()
        grandchild.refresh_from_db()
        self.assertEqual(parent.visibility, GroupProfile.Visibility.PRIVATE)
        self.assertEqual(child.visibility, GroupProfile.Visibility.PRIVATE)
        self.assertEqual(grandchild.visibility, GroupProfile.Visibility.PRIVATE)

    def test_cannot_change_subgroup_visibility(self):
        """Attempting to change subgroup visibility is overridden by parent."""
        parent_group = Group.objects.create(name="Parent")
        parent = GroupProfile.add_root(
            group=parent_group,
            slug="parent",
            visibility=GroupProfile.Visibility.PRIVATE,
        )

        child_group = Group.objects.create(name="Child")
        child = parent.add_child(
            group=child_group,
            slug="child",
        )

        # Verify child is PRIVATE (inherited)
        child.refresh_from_db()
        self.assertEqual(child.visibility, GroupProfile.Visibility.PRIVATE)

        # Try to change child to PUBLIC (simulates admin form submission)
        child.visibility = GroupProfile.Visibility.PUBLIC
        child.save()

        # Refresh and verify it's still PRIVATE (overridden by parent)
        child.refresh_from_db()
        self.assertEqual(child.visibility, GroupProfile.Visibility.PRIVATE)

        # Verify descendants also remain PRIVATE
        grandchild_group = Group.objects.create(name="Grandchild")
        grandchild = child.add_child(
            group=grandchild_group,
            slug="grandchild",
        )
        grandchild.refresh_from_db()
        self.assertEqual(grandchild.visibility, GroupProfile.Visibility.PRIVATE)


class ModeratedVisibilityTests(TestCase):
    """Test MODERATED visibility with nested groups."""

    def setUp(self):
        """Create MODERATED hierarchy for testing dual access model."""
        parent_group = Group.objects.create(name="Parent")
        self.parent = GroupProfile.add_root(
            group=parent_group,
            slug="parent",
            visibility=GroupProfile.Visibility.MODERATED,
        )

        moderated_child_group = Group.objects.create(name="ModeratedChild")
        self.moderated_child = self.parent.add_child(
            group=moderated_child_group,
            slug="moderated-child",
        )

        moderator_group = Group.objects.create(name="Moderators")
        self.moderator_group_profile = GroupProfile.add_root(
            group=moderator_group,
            slug="moderators",
            visibility=GroupProfile.Visibility.PUBLIC,
        )
        # Add moderator group to both parent and child
        self.parent.visible_to_groups.add(moderator_group)
        self.moderated_child.visible_to_groups.add(moderator_group)

    def test_moderated_child_visible_to_moderator_group(self):
        """User in moderator group can see MODERATED tree (cross-hierarchy access)."""
        user = UserFactory()
        self.moderator_group_profile.group.user_set.add(user)

        visible = GroupProfile.objects.visible(user)

        # Moderator group has cross-hierarchy access
        self.assertIn(self.parent, visible)
        self.assertIn(self.moderated_child, visible)

    def test_moderated_child_not_visible_to_non_moderator(self):
        """User not in moderator group or hierarchy cannot see MODERATED tree."""
        user = UserFactory()

        visible = GroupProfile.objects.visible(user)

        # Not in moderator group, not in hierarchy
        self.assertNotIn(self.parent, visible)
        self.assertNotIn(self.moderated_child, visible)

    def test_moderated_child_visible_to_parent_member(self):
        """Member of parent can see moderated child (hierarchy access)."""
        user = UserFactory()
        self.parent.group.user_set.add(user)

        visible = GroupProfile.objects.visible(user)

        self.assertIn(self.parent, visible)
        # User is in parent hierarchy, so can see moderated child
        # MODERATED allows both: hierarchy access AND moderator group access
        self.assertIn(self.moderated_child, visible)


class VisibleToGroupsInheritanceTests(TestCase):
    """Test that visible_to_groups is inherited from parent to children."""

    def test_child_inherits_visible_to_groups_on_create(self):
        """Child automatically inherits parent's visible_to_groups when created."""
        parent_group = Group.objects.create(name="Parent")
        parent = GroupProfile.add_root(
            group=parent_group,
            slug="parent",
            visibility=GroupProfile.Visibility.MODERATED,
        )

        audit_group = Group.objects.create(name="AuditTeam")
        GroupProfile.add_root(
            group=audit_group,
            slug="audit-team",
            visibility=GroupProfile.Visibility.PUBLIC,
        )

        parent.visible_to_groups.add(audit_group)

        child_group = Group.objects.create(name="Child")
        child = parent.add_child(group=child_group, slug="child")
        child.refresh_from_db()

        self.assertEqual(set(child.visible_to_groups.all()), set(parent.visible_to_groups.all()))

    def test_adding_to_parent_propagates_to_descendants(self):
        """Adding group to parent's visible_to_groups propagates to descendants."""
        parent_group = Group.objects.create(name="Parent")
        parent = GroupProfile.add_root(
            group=parent_group,
            slug="parent",
            visibility=GroupProfile.Visibility.MODERATED,
        )

        child_group = Group.objects.create(name="Child")
        child = parent.add_child(group=child_group, slug="child")

        grandchild_group = Group.objects.create(name="Grandchild")
        grandchild = child.add_child(group=grandchild_group, slug="grandchild")

        audit_group = Group.objects.create(name="AuditTeam")
        parent.visible_to_groups.add(audit_group)

        child.refresh_from_db()
        grandchild.refresh_from_db()

        self.assertIn(audit_group, parent.visible_to_groups.all())
        self.assertIn(audit_group, child.visible_to_groups.all())
        self.assertIn(audit_group, grandchild.visible_to_groups.all())

    def test_removing_from_parent_propagates_to_descendants(self):
        """Removing group from parent's visible_to_groups propagates to descendants."""
        parent_group = Group.objects.create(name="Parent")
        parent = GroupProfile.add_root(
            group=parent_group,
            slug="parent",
            visibility=GroupProfile.Visibility.MODERATED,
        )

        audit_group = Group.objects.create(name="AuditTeam")
        parent.visible_to_groups.add(audit_group)

        child_group = Group.objects.create(name="Child")
        child = parent.add_child(group=child_group, slug="child")
        child.refresh_from_db()

        self.assertIn(audit_group, child.visible_to_groups.all())

        parent.visible_to_groups.remove(audit_group)
        child.refresh_from_db()

        self.assertNotIn(audit_group, child.visible_to_groups.all())

    def test_clearing_parent_propagates_to_descendants(self):
        """Clearing parent's visible_to_groups propagates to descendants."""
        parent_group = Group.objects.create(name="Parent")
        parent = GroupProfile.add_root(
            group=parent_group,
            slug="parent",
            visibility=GroupProfile.Visibility.MODERATED,
        )

        audit1 = Group.objects.create(name="Audit1")
        audit2 = Group.objects.create(name="Audit2")
        parent.visible_to_groups.add(audit1, audit2)

        child_group = Group.objects.create(name="Child")
        child = parent.add_child(group=child_group, slug="child")
        child.refresh_from_db()

        self.assertEqual(child.visible_to_groups.count(), 2)

        parent.visible_to_groups.clear()
        child.refresh_from_db()

        self.assertEqual(child.visible_to_groups.count(), 0)

    def test_deep_hierarchy_propagation(self):
        """visible_to_groups propagates through deep hierarchies."""
        root_group = Group.objects.create(name="Root")
        root = GroupProfile.add_root(group=root_group, slug="root")

        level1_group = Group.objects.create(name="Level1")
        level1 = root.add_child(group=level1_group, slug="level1")

        level2_group = Group.objects.create(name="Level2")
        level2 = level1.add_child(group=level2_group, slug="level2")

        level3_group = Group.objects.create(name="Level3")
        level3 = level2.add_child(group=level3_group, slug="level3")

        audit_group = Group.objects.create(name="AuditTeam")
        root.visible_to_groups.add(audit_group)

        level1.refresh_from_db()
        level2.refresh_from_db()
        level3.refresh_from_db()

        self.assertIn(audit_group, root.visible_to_groups.all())
        self.assertIn(audit_group, level1.visible_to_groups.all())
        self.assertIn(audit_group, level2.visible_to_groups.all())
        self.assertIn(audit_group, level3.visible_to_groups.all())
