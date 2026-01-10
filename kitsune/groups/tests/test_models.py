from kitsune.groups.models import Group, GroupProfile
from kitsune.groups.tests import GroupFactory, GroupProfileFactory
from kitsune.sumo.tests import TestCase
from kitsune.users.tests import UserFactory


class GroupVisibilityTests(TestCase):
    """Tests for private group visibility and access control."""

    def setUp(self):
        super().setUp()
        self.regular_user = UserFactory()
        self.member1_user = UserFactory()
        self.member2_user = UserFactory()
        self.leader1_user = UserFactory()
        self.leader2_user = UserFactory()
        self.superuser = UserFactory(is_superuser=True)

        self.private_group1 = GroupProfileFactory(is_private=True)
        self.private_group1.group.user_set.add(self.member1_user)
        self.private_group1.group.user_set.add(UserFactory())
        self.private_group1.leaders.add(self.leader1_user)
        self.private_group1.leaders.add(UserFactory())
        self.private_group2 = GroupProfileFactory(is_private=True)
        self.private_group2.group.user_set.add(self.member1_user)
        self.private_group2.group.user_set.add(self.member2_user)
        self.private_group2.leaders.add(self.leader1_user)
        self.private_group2.leaders.add(self.leader2_user)
        self.private_group3 = GroupProfileFactory(is_private=True)

        public_group1 = GroupProfileFactory(is_private=False)
        public_group2 = GroupProfileFactory(is_private=False)
        # Groups without a profile are considered public.
        group_without_profile = GroupFactory()

        # Ensure that the Staff Content Team group profile has a slug.
        staff_content_group = GroupProfile.objects.get(group__name="Staff Content Team")
        staff_content_group.save()

        self.set_of_public_slugs = {
            public_group1.slug,
            public_group2.slug,
            staff_content_group.slug,
        }
        self.set_of_public_names = {
            public_group1.group.name,
            public_group2.group.name,
            staff_content_group.group.name,
            group_without_profile.name,
        }

    def test_group_profiles_visibility_anonymous_user(self):
        qs_profiles = GroupProfile.objects.visible()
        self.assertEqual(qs_profiles.count(), 3)
        self.assertEqual(set(qs_profiles.values_list("slug", flat=True)), self.set_of_public_slugs)

    def test_group_profiles_visibility_user_without_access(self):
        qs_profiles = GroupProfile.objects.visible(self.regular_user)
        self.assertEqual(qs_profiles.count(), 3)
        self.assertEqual(set(qs_profiles.values_list("slug", flat=True)), self.set_of_public_slugs)

    def test_group_profiles_visibility_member(self):
        qs_profiles = GroupProfile.objects.visible(self.member1_user)
        self.assertEqual(qs_profiles.count(), 5)
        self.assertEqual(
            set(qs_profiles.values_list("slug", flat=True)),
            self.set_of_public_slugs | {self.private_group1.slug, self.private_group2.slug},
        )

        qs_profiles = GroupProfile.objects.visible(self.member2_user)
        self.assertEqual(qs_profiles.count(), 4)
        self.assertEqual(
            set(qs_profiles.values_list("slug", flat=True)),
            self.set_of_public_slugs | {self.private_group2.slug},
        )

    def test_group_profiles_visibility_leader(self):
        qs_profiles = GroupProfile.objects.visible(self.leader1_user)
        self.assertEqual(qs_profiles.count(), 5)
        self.assertEqual(
            set(qs_profiles.values_list("slug", flat=True)),
            self.set_of_public_slugs | {self.private_group1.slug, self.private_group2.slug},
        )

        qs_profiles = GroupProfile.objects.visible(self.leader2_user)
        self.assertEqual(qs_profiles.count(), 4)
        self.assertEqual(
            set(qs_profiles.values_list("slug", flat=True)),
            self.set_of_public_slugs | {self.private_group2.slug},
        )

    def test_group_profiles_visibility_superuser(self):
        qs_profiles = GroupProfile.objects.visible(self.superuser)
        self.assertEqual(qs_profiles.count(), 6)
        self.assertEqual(
            set(qs_profiles.values_list("slug", flat=True)),
            self.set_of_public_slugs
            | {
                self.private_group1.slug,
                self.private_group2.slug,
                self.private_group3.slug,
            },
        )

    def test_groups_visibility_anonymous_user(self):
        qs_groups = GroupProfile.filter_by_visibility(Group.objects.all())
        self.assertEqual(qs_groups.count(), 4)
        self.assertEqual(set(qs_groups.values_list("name", flat=True)), self.set_of_public_names)

    def test_groups_visibility_user_without_access(self):
        qs_groups = GroupProfile.filter_by_visibility(Group.objects.all(), self.regular_user)
        self.assertEqual(qs_groups.count(), 4)
        self.assertEqual(set(qs_groups.values_list("name", flat=True)), self.set_of_public_names)

    def test_groups_visibility_member(self):
        qs_groups = GroupProfile.filter_by_visibility(Group.objects.all(), self.member1_user)
        self.assertEqual(qs_groups.count(), 6)
        self.assertEqual(
            set(qs_groups.values_list("name", flat=True)),
            self.set_of_public_names
            | {self.private_group1.group.name, self.private_group2.group.name},
        )

        qs_groups = GroupProfile.filter_by_visibility(Group.objects.all(), self.member2_user)
        self.assertEqual(qs_groups.count(), 5)
        self.assertEqual(
            set(qs_groups.values_list("name", flat=True)),
            self.set_of_public_names | {self.private_group2.group.name},
        )

    def test_groups_visibility_leader(self):
        qs_groups = GroupProfile.filter_by_visibility(Group.objects.all(), self.leader1_user)
        self.assertEqual(qs_groups.count(), 6)
        self.assertEqual(
            set(qs_groups.values_list("name", flat=True)),
            self.set_of_public_names
            | {self.private_group1.group.name, self.private_group2.group.name},
        )

        qs_groups = GroupProfile.filter_by_visibility(Group.objects.all(), self.leader2_user)
        self.assertEqual(qs_groups.count(), 5)
        self.assertEqual(
            set(qs_groups.values_list("name", flat=True)),
            self.set_of_public_names | {self.private_group2.group.name},
        )

    def test_groups_visibility_superuser(self):
        qs_groups = GroupProfile.filter_by_visibility(Group.objects.all(), self.superuser)
        self.assertEqual(qs_groups.count(), 7)
        self.assertEqual(
            set(qs_groups.values_list("name", flat=True)),
            self.set_of_public_names
            | {
                self.private_group1.group.name,
                self.private_group2.group.name,
                self.private_group3.group.name,
            },
        )
