from datetime import timedelta
from unittest.mock import patch

from django.test import override_settings
from django.utils import timezone

from kitsune.groups.models import GroupProfile
from kitsune.groups.tasks import remove_inactive_users_from_groups
from kitsune.groups.tests import GroupProfileFactory
from kitsune.sumo.tests import TestCase
from kitsune.users.models import Deactivation
from kitsune.users.tests import GroupFactory, UserFactory


@override_settings(INACTIVE_GROUP_MEMBER_RETENTION_DAYS=180)
class RemoveInactiveUsersTests(TestCase):
    """Test the remove_inactive_users_from_groups periodic task."""

    def setUp(self):
        self.moderator = UserFactory()
        self.group_profile = GroupProfileFactory(slug="test-group")

    def _deactivate(self, user, days_ago):
        """Helper: mark user inactive and record a Deactivation entry."""
        user.is_active = False
        user.save()
        Deactivation.objects.create(
            user=user,
            moderator=self.moderator,
            date=timezone.now() - timedelta(days=days_ago),
        )

    def test_old_deactivation_removes_member_and_leader(self):
        """User deactivated more than the threshold is removed from membership and leadership."""
        user = UserFactory()
        self.group_profile.group.user_set.add(user)
        self.group_profile.leaders.add(user)
        # Also add a second leader so the root group is not left leaderless
        extra_leader = UserFactory()
        self.group_profile.leaders.add(extra_leader)

        self._deactivate(user, days_ago=181)

        remove_inactive_users_from_groups()

        self.assertFalse(self.group_profile.group.user_set.filter(pk=user.pk).exists())
        self.assertFalse(self.group_profile.leaders.filter(pk=user.pk).exists())

    def test_recent_deactivation_is_not_removed(self):
        """User deactivated less than the threshold is NOT removed."""
        user = UserFactory()
        self.group_profile.group.user_set.add(user)

        self._deactivate(user, days_ago=179)

        remove_inactive_users_from_groups()

        self.assertTrue(self.group_profile.group.user_set.filter(pk=user.pk).exists())

    def test_inactive_user_without_deactivation_record_is_not_removed(self):
        """User with is_active=False but no Deactivation record is NOT removed."""
        user = UserFactory()
        self.group_profile.group.user_set.add(user)

        # No Deactivation record is created.
        user.is_active = False
        user.save()

        remove_inactive_users_from_groups()

        self.assertTrue(self.group_profile.group.user_set.filter(pk=user.pk).exists())

    def test_active_user_with_old_deactivation_record_is_not_removed(self):
        """Active user with a stale Deactivation record is NOT removed."""
        user = UserFactory()
        self.group_profile.group.user_set.add(user)

        # Create a Deactivation record but keep user active (simulates reactivation).
        Deactivation.objects.create(
            user=user,
            moderator=self.moderator,
            date=timezone.now() - timedelta(days=210),
        )

        remove_inactive_users_from_groups()

        self.assertTrue(self.group_profile.group.user_set.filter(pk=user.pk).exists())

    def test_only_leader_of_root_group_is_not_removed_nor_is_membership(self):
        """Last leader of a root group is NOT removed, and membership is retained."""
        user = UserFactory()
        self.group_profile.group.user_set.add(user)
        self.group_profile.leaders.add(user)

        self._deactivate(user, days_ago=210)

        with patch("kitsune.groups.tasks.log") as mock_log:
            remove_inactive_users_from_groups()
            mock_log.warning.assert_called_once_with(
                "Skipping the removal of inactive leader(s) from the root group "
                f'"{self.group_profile}" because it would become leaderless.'
            )

        # Leader assignment should NOT be removed (roots must have at least one leader).
        self.assertTrue(self.group_profile.leaders.filter(pk=user.pk).exists())
        # The leader's membership should be retained as well.
        self.assertTrue(self.group_profile.group.user_set.filter(pk=user.pk).exists())

    def test_one_of_two_leaders_of_root_group_is_removed(self):
        """When a root group has two leaders, the deactivated one IS removed."""
        active_leader = UserFactory()
        self.group_profile.leaders.add(active_leader)

        deactivated_leader = UserFactory()
        self.group_profile.leaders.add(deactivated_leader)
        self.group_profile.group.user_set.add(deactivated_leader)

        self._deactivate(deactivated_leader, days_ago=210)

        remove_inactive_users_from_groups()

        # Deactivated leader removed
        self.assertFalse(self.group_profile.leaders.filter(pk=deactivated_leader.pk).exists())
        # Active leader retained
        self.assertTrue(self.group_profile.leaders.filter(pk=active_leader.pk).exists())
        # Membership also removed
        self.assertFalse(
            self.group_profile.group.user_set.filter(pk=deactivated_leader.pk).exists()
        )

    def test_subgroup_only_leader_is_removed(self):
        """The only leader of a subgroup IS removed (subgroups can be leaderless)."""
        subgroup_profile = self.group_profile.add_child(
            group=GroupFactory(),
            slug="sub-group",
            visibility=GroupProfile.Visibility.PUBLIC,
        )

        user = UserFactory()
        subgroup_profile.group.user_set.add(user)
        subgroup_profile.leaders.add(user)

        self._deactivate(user, days_ago=210)

        with patch("kitsune.groups.tasks.log") as mock_log:
            remove_inactive_users_from_groups()
            mock_log.warning.assert_not_called()

        # Leader assignment SHOULD be removed since it's a subgroup (depth > 1).
        self.assertFalse(subgroup_profile.leaders.filter(pk=user.pk).exists())

    def test_all_multiple_leaders_of_root_group_are_retained(self):
        """If a root group has multiple leaders and ALL are inactive, none are removed."""
        leader1 = UserFactory()
        leader2 = UserFactory()
        self.group_profile.leaders.add(leader1, leader2)

        self._deactivate(leader1, days_ago=210)
        self._deactivate(leader2, days_ago=210)

        remove_inactive_users_from_groups()

        # Both should be kept to prevent a leaderless root group.
        self.assertTrue(self.group_profile.leaders.filter(pk=leader1.pk).exists())
        self.assertTrue(self.group_profile.leaders.filter(pk=leader2.pk).exists())

    def test_latest_deactivation_record_is_respected(self):
        """User with an old AND a recent Deactivation record is NOT removed."""
        user = UserFactory()
        self.group_profile.group.user_set.add(user)
        user.is_active = False
        user.save()

        # Old deactivation (should be ignored)
        Deactivation.objects.create(
            user=user,
            moderator=self.moderator,
            date=timezone.now() - timedelta(days=210),
        )
        # Recent deactivation (should prevent removal)
        Deactivation.objects.create(
            user=user,
            moderator=self.moderator,
            date=timezone.now() - timedelta(days=30),
        )

        remove_inactive_users_from_groups()

        self.assertTrue(self.group_profile.group.user_set.filter(pk=user.pk).exists())
