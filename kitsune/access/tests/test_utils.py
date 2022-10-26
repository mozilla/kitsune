from guardian.shortcuts import assign_perm

from kitsune.access.utils import has_perm
from kitsune.forums.tests import ForumFactory
from kitsune.sumo.tests import TestCase
from kitsune.users.tests import UserFactory, GroupFactory


class HasPermTests(TestCase):
    def test_admin_perm_thread(self):
        """Super user can do anything on any forum."""

        forum = ForumFactory(restrict_viewing=True, restrict_posting=True)

        user = UserFactory()
        admin = UserFactory(is_staff=True, is_superuser=True)

        # Loop over all forums perms and both forums
        perms = (
            "forums.view_in_forum",
            "forums.post_in_forum",
            "forums.delete_forum_thread",
            "forums.edit_forum_thread",
            "forums.lock_forum_thread",
            "forums.move_forum_thread",
            "forums.sticky_forum_thread",
            "forums.delete_forum_thread_post",
            "forums.edit_forum_thread_post",
        )

        for perm in perms:
            self.assertFalse(has_perm(user, perm, forum))
            self.assertTrue(has_perm(admin, perm, forum))

    def test_has_perm_per_object(self):
        """Assert has_perm checks per-object permissions correctly."""

        user1 = UserFactory()
        user2 = UserFactory()
        user3 = UserFactory()
        group = GroupFactory()
        group.user_set.add(user2)

        f1 = ForumFactory(restrict_viewing=True)
        assign_perm("forums.view_in_forum", user1, f1)
        f2 = ForumFactory(restrict_viewing=True)
        assign_perm("forums.view_in_forum", group, f2)
        f3 = ForumFactory(restrict_viewing=True, restrict_posting=True)
        assign_perm("forums.post_in_forum", user1, f3)
        assign_perm("forums.post_in_forum", group, f3)

        # Test permission assigned to a user.
        self.assertTrue(has_perm(user1, "forums.view_in_forum", f1))
        self.assertFalse(has_perm(user1, "forums.view_in_forum", f2))
        self.assertFalse(has_perm(user1, "forums.view_in_forum", f3))
        self.assertFalse(has_perm(user1, "forums.post_in_forum", f1))
        self.assertFalse(has_perm(user1, "forums.post_in_forum", f2))
        self.assertTrue(has_perm(user1, "forums.post_in_forum", f3))

        # Test permission assigned via a group.
        self.assertFalse(has_perm(user2, "forums.view_in_forum", f1))
        self.assertTrue(has_perm(user2, "forums.view_in_forum", f2))
        self.assertFalse(has_perm(user2, "forums.view_in_forum", f3))
        self.assertFalse(has_perm(user2, "forums.post_in_forum", f1))
        self.assertFalse(has_perm(user2, "forums.post_in_forum", f2))
        self.assertTrue(has_perm(user2, "forums.post_in_forum", f3))

        # Test that other users do not have permission.
        self.assertFalse(has_perm(user3, "forums.view_in_forum", f1))
        self.assertFalse(has_perm(user3, "forums.view_in_forum", f2))
        self.assertFalse(has_perm(user3, "forums.view_in_forum", f3))
        self.assertFalse(has_perm(user3, "forums.post_in_forum", f1))
        self.assertFalse(has_perm(user3, "forums.post_in_forum", f2))
        self.assertFalse(has_perm(user3, "forums.post_in_forum", f3))

    def test_has_perm_when_gobal(self):
        """Assert has_perm checks global permissions correctly."""

        user1 = UserFactory()
        user2 = UserFactory()
        f1 = ForumFactory(restrict_viewing=True)
        f2 = ForumFactory(restrict_viewing=True)

        assign_perm("forums.view_in_forum", user1)
        assign_perm("forums.view_in_forum", user2, f2)

        # User1 should have access to all restricted forums.
        self.assertTrue(has_perm(user1, "forums.view_in_forum", f1))
        self.assertTrue(has_perm(user1, "forums.view_in_forum", f2))

        # User2 should only have access to the second restricted forum.
        self.assertFalse(has_perm(user2, "forums.view_in_forum", f1))
        self.assertTrue(has_perm(user2, "forums.view_in_forum", f2))
