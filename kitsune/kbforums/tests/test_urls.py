from nose.tools import eq_

from kitsune.kbforums.tests import KBForumTestCase
from kitsune.kbforums.tests import ThreadFactory
from kitsune.sumo.tests import get
from kitsune.sumo.tests import post
from kitsune.users.tests import add_permission
from kitsune.users.tests import UserFactory
from kitsune.wiki.tests import DocumentFactory


class KBBelongsTestCase(KBForumTestCase):
    """
    Mixing and matching thread, forum, and post data in URLs should fail.
    """

    def setUp(self):
        super(KBBelongsTestCase, self).setUp()
        u = UserFactory()
        self.doc = DocumentFactory(title="spam")
        self.doc_2 = DocumentFactory(title="eggs")
        self.thread = ThreadFactory(creator=u, document=self.doc, is_locked=False)
        self.thread_2 = ThreadFactory(creator=u, document=self.doc_2, is_locked=False)
        permissions = ("sticky_thread", "lock_thread", "delete_thread", "delete_post")
        for permission in permissions:
            add_permission(u, self.thread, permission)
        self.post = self.thread.new_post(creator=self.thread.creator, content="foo")
        self.client.login(username=u.username, password="testpass")

    def test_posts_thread_belongs_to_document(self):
        """Posts view - thread belongs to document."""
        r = get(self.client, "wiki.discuss.posts", args=[self.doc_2.slug, self.thread.id])
        eq_(404, r.status_code)

    def test_reply_thread_belongs_to_document(self):
        """Reply action - thread belongs to document."""
        r = post(self.client, "wiki.discuss.reply", {}, args=[self.doc_2.slug, self.thread.id])
        eq_(404, r.status_code)

    def test_locked_thread_belongs_to_document(self):
        """Lock action - thread belongs to document."""
        r = post(
            self.client, "wiki.discuss.lock_thread", {}, args=[self.doc_2.slug, self.thread.id]
        )
        eq_(404, r.status_code)

    def test_sticky_thread_belongs_to_document(self):
        """Sticky action - thread belongs to document."""
        r = post(
            self.client, "wiki.discuss.sticky_thread", {}, args=[self.doc_2.slug, self.thread.id]
        )
        eq_(404, r.status_code)

    def test_edit_thread_belongs_to_document(self):
        """Edit thread action - thread belongs to document."""
        r = get(self.client, "wiki.discuss.edit_thread", args=[self.doc_2.slug, self.thread.id])
        eq_(404, r.status_code)

    def test_delete_thread_belongs_to_document(self):
        """Delete thread action - thread belongs to document."""
        r = get(self.client, "wiki.discuss.delete_thread", args=[self.doc_2.slug, self.thread.id])
        eq_(404, r.status_code)

    def test_edit_post_belongs_to_thread_and_document(self):
        """
        Edit post action - post belongs to thread and thread belongs to
        forum.
        """
        r = get(
            self.client,
            "wiki.discuss.edit_post",
            args=[self.doc_2.slug, self.thread.id, self.post.id],
        )
        eq_(404, r.status_code)

        r = get(
            self.client,
            "wiki.discuss.edit_post",
            args=[self.doc.slug, self.thread_2.id, self.post.id],
        )
        eq_(404, r.status_code)

    def test_delete_post_belongs_to_thread_and_document(self):
        """
        Delete post action - post belongs to thread and thread belongs to
        forum.
        """
        r = get(
            self.client,
            "wiki.discuss.delete_post",
            args=[self.doc_2.slug, self.thread.id, self.post.id],
        )
        eq_(404, r.status_code)

        r = get(
            self.client,
            "wiki.discuss.delete_post",
            args=[self.doc.slug, self.thread_2.id, self.post.id],
        )
        eq_(404, r.status_code)
