from guardian.shortcuts import assign_perm

from kitsune.forums.tests import ForumFactory, PostFactory, ThreadFactory
from kitsune.sumo.tests import TestCase, get, post
from kitsune.users.tests import GroupFactory, UserFactory


class BelongsTestCase(TestCase):
    """
    Mixing and matching thread, forum, and post data in URLs should fail.
    """

    def test_posts_thread_belongs_to_forum(self):
        """Posts view - redirect if thread does not belong to forum."""
        f = ForumFactory()
        t = ThreadFactory()  # Thread belongs to a different forum

        r = get(self.client, "forums.posts", args=[f.slug, t.id])
        self.assertEqual(200, r.status_code)
        u = r.redirect_chain[0][0]
        assert u.endswith(t.get_absolute_url())

    def test_reply_thread_belongs_to_forum(self):
        """Reply action - thread belongs to forum."""
        f = ForumFactory()
        t = ThreadFactory()  # Thread belongs to a different forum
        u = UserFactory()

        self.client.login(username=u.username, password="testpass")
        r = post(self.client, "forums.reply", {}, args=[f.slug, t.id])
        self.assertEqual(404, r.status_code)

    def test_locked_thread_belongs_to_forum(self):
        """Lock action - thread belongs to forum."""
        f = ForumFactory()
        t = ThreadFactory()  # Thread belongs to a different forum
        u = UserFactory()

        # Give the user the permission to lock threads.
        g = GroupFactory()
        g.user_set.add(u)
        assign_perm("forums.lock_forum_thread", g, f)
        assign_perm("forums.lock_forum_thread", g, t.forum)

        self.client.login(username=u.username, password="testpass")
        r = post(self.client, "forums.lock_thread", {}, args=[f.slug, t.id])
        self.assertEqual(404, r.status_code)

    def test_sticky_thread_belongs_to_forum(self):
        """Sticky action - thread belongs to forum."""
        f = ForumFactory()
        t = ThreadFactory()  # Thread belongs to a different forum
        u = UserFactory()

        # Give the user the permission to sticky threads.
        g = GroupFactory()
        g.user_set.add(u)
        assign_perm("forums.sticky_forum_thread", g, f)
        assign_perm("forums.sticky_forum_thread", g, t.forum)

        self.client.login(username=u.username, password="testpass")
        r = post(self.client, "forums.sticky_thread", {}, args=[f.slug, t.id])
        self.assertEqual(404, r.status_code)

    def test_edit_thread_belongs_to_forum(self):
        """Edit thread action - thread belongs to forum."""
        f = ForumFactory()
        t = ThreadFactory()  # Thread belongs to a different forum
        u = t.creator

        self.client.login(username=u.username, password="testpass")
        r = get(self.client, "forums.edit_thread", args=[f.slug, t.id])
        self.assertEqual(404, r.status_code)

    def test_delete_thread_belongs_to_forum(self):
        """Delete thread action - thread belongs to forum."""
        f = ForumFactory()
        t = ThreadFactory()  # Thread belongs to a different forum
        u = UserFactory()

        # Give the user the permission to delete threads.
        g = GroupFactory()
        g.user_set.add(u)
        assign_perm("forums.delete_forum_thread", g, f)
        assign_perm("forums.delete_forum_thread", g, t.forum)

        self.client.login(username=u.username, password="testpass")
        r = get(self.client, "forums.delete_thread", args=[f.slug, t.id])
        self.assertEqual(404, r.status_code)

    def test_edit_post_belongs_to_thread_and_forum(self):
        # Edit post action - post belongs to thread and thread belongs
        # to forum.
        f = ForumFactory()
        t = ThreadFactory(forum=f)
        # Post belongs to a different forum and thread.
        p = PostFactory()
        u = p.author

        self.client.login(username=u.username, password="testpass")

        # Post isn't in the passed forum:
        r = get(self.client, "forums.edit_post", args=[f.slug, p.thread.id, p.id])
        self.assertEqual(404, r.status_code)

        # Post isn't in the passed thread:
        r = get(self.client, "forums.edit_post", args=[p.thread.forum.slug, t.id, p.id])
        self.assertEqual(404, r.status_code)

    def test_delete_post_belongs_to_thread_and_forum(self):
        # Delete post action - post belongs to thread and thread
        # belongs to forum.
        f = ForumFactory()
        t = ThreadFactory(forum=f)
        # Post belongs to a different forum and thread.
        p = PostFactory()
        u = p.author

        # Give the user the permission to delete posts.
        g = GroupFactory()
        g.user_set.add(u)
        assign_perm("forums.delete_forum_thread_post", g, f)
        assign_perm("forums.delete_forum_thread_post", g, p.thread.forum)

        self.client.login(username=u.username, password="testpass")

        # Post isn't in the passed forum:
        r = get(self.client, "forums.delete_post", args=[f.slug, p.thread.id, p.id])
        self.assertEqual(404, r.status_code)

        # Post isn't in the passed thread:
        r = get(self.client, "forums.delete_post", args=[p.thread.forum.slug, t.id, p.id])
        self.assertEqual(404, r.status_code)
