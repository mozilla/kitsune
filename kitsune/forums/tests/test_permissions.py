from guardian.shortcuts import assign_perm

from kitsune.access.utils import has_perm
from kitsune.forums.tests import ForumFactory
from kitsune.sumo.tests import TestCase
from kitsune.users.tests import UserFactory, GroupFactory


class ForumTestPermissions(TestCase):
    """Make sure access helpers work on the forums."""

    def setUp(self):
        self.group = GroupFactory()

        # Set up forum_1
        self.forum_1 = ForumFactory()
        permission_names = [
            "forums.delete_forum_thread",
            "forums.edit_forum_thread",
            "forums.move_forum_thread",
            "forums.sticky_forum_thread",
            "forums.delete_forum_thread_post",
            "forums.edit_forum_thread_post",
        ]
        for name in permission_names:
            assign_perm(name, self.group, self.forum_1)

        # Set up forum_2
        self.forum_2 = ForumFactory()
        assign_perm("forums.move_forum_thread", self.group, self.forum_2)

    def test_has_perm_thread_edit(self):
        """User in group can edit thread in forum_1, but not in forum_2."""
        user = UserFactory()
        self.group.user_set.add(user)
        self.assertTrue(has_perm(user, "forums.edit_forum_thread", self.forum_1))
        self.assertFalse(has_perm(user, "forums.edit_forum_thread", self.forum_2))

    def test_has_perm_thread_delete(self):
        """User in group can delete thread in forum_1, but not in forum_2."""
        user = UserFactory()
        self.group.user_set.add(user)
        self.assertTrue(has_perm(user, "forums.delete_forum_thread", self.forum_1))
        self.assertFalse(has_perm(user, "forums.delete_forum_thread", self.forum_2))

    def test_has_perm_thread_sticky(self):
        """
        User in group can change sticky status of thread in forum_1, but not in forum_2.
        """
        user = UserFactory()
        self.group.user_set.add(user)
        self.assertTrue(has_perm(user, "forums.sticky_forum_thread", self.forum_1))
        self.assertFalse(has_perm(user, "forums.sticky_forum_thread", self.forum_2))

    def test_has_perm_thread_locked(self):
        """User in group has no permission to change locked status in forum_1."""
        user = UserFactory()
        self.group.user_set.add(user)
        self.assertFalse(has_perm(user, "forums.lock_forum_thread", self.forum_1))

    def test_has_perm_post_edit(self):
        """User in group can edit any post in forum_1, but not in forum_2."""
        user = UserFactory()
        self.group.user_set.add(user)
        self.assertTrue(has_perm(user, "forums.edit_forum_thread_post", self.forum_1))
        self.assertFalse(has_perm(user, "forums.edit_forum_thread_post", self.forum_2))

    def test_has_perm_post_delete(self):
        """User in group can delete posts in forum_1, but not in forum_2."""
        user = UserFactory()
        self.group.user_set.add(user)
        self.assertTrue(has_perm(user, "forums.delete_forum_thread_post", self.forum_1))
        self.assertFalse(has_perm(user, "forums.delete_forum_thread_post", self.forum_2))

    def test_no_perm_thread_delete(self):
        """User not in group cannot delete thread in any forum."""
        user = UserFactory()
        self.assertFalse(has_perm(user, "forums.delete_forum_thread", self.forum_1))
        self.assertFalse(has_perm(user, "forums.delete_forum_thread", self.forum_2))
