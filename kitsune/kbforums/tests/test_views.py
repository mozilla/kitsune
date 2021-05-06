from nose.tools import eq_

from kitsune.kbforums.models import Thread
from kitsune.kbforums.tests import KBForumTestCase, ThreadFactory
from kitsune.kbforums.events import NewThreadEvent, NewPostEvent
from kitsune.sumo.tests import get, post
from kitsune.users.tests import UserFactory, add_permission
from kitsune.wiki.tests import DocumentFactory


class ThreadTests(KBForumTestCase):
    """Test thread views."""

    def test_watch_forum(self):
        """Watch then unwatch a forum."""
        u = UserFactory()
        self.client.login(username=u.username, password="testpass")

        d = DocumentFactory()
        post(self.client, "wiki.discuss.watch_forum", {"watch": "yes"}, args=[d.slug])
        assert NewThreadEvent.is_notifying(u, d)
        # NewPostEvent is not notifying.
        t = ThreadFactory(document=d)
        p = t.new_post(creator=t.creator, content="test")
        assert not NewPostEvent.is_notifying(u, p)

        post(self.client, "wiki.discuss.watch_forum", {"watch": "no"}, args=[d.slug])
        assert not NewThreadEvent.is_notifying(u, d)

    def test_watch_thread(self):
        """Watch then unwatch a thread."""
        u = UserFactory()
        self.client.login(username=u.username, password="testpass")

        t = ThreadFactory()
        post(
            self.client,
            "wiki.discuss.watch_thread",
            {"watch": "yes"},
            args=[t.document.slug, t.id],
        )
        assert NewPostEvent.is_notifying(u, t)
        # NewThreadEvent is not notifying.
        assert not NewThreadEvent.is_notifying(u, t.document)

        post(
            self.client, "wiki.discuss.watch_thread", {"watch": "no"}, args=[t.document.slug, t.id]
        )
        assert not NewPostEvent.is_notifying(u, t)

    def test_edit_thread(self):
        """Changing thread title works."""
        u = UserFactory()
        self.client.login(username=u.username, password="testpass")

        d = DocumentFactory()
        t = ThreadFactory(title="Sticky Thread", document=d, creator=u)
        post(
            self.client, "wiki.discuss.edit_thread", {"title": "A new title"}, args=[d.slug, t.id]
        )
        edited_t = d.thread_set.get(pk=t.id)

        eq_("Sticky Thread", t.title)
        eq_("A new title", edited_t.title)

    def test_edit_thread_moderator(self):
        """Editing post as a moderator works."""
        u = UserFactory()
        add_permission(u, Thread, "change_thread")
        t = ThreadFactory(title="Sticky Thread")
        d = t.document
        self.client.login(username=u.username, password="testpass")

        eq_("Sticky Thread", t.title)

        r = post(
            self.client, "wiki.discuss.edit_thread", {"title": "new title"}, args=[d.slug, t.id]
        )
        eq_(200, r.status_code)

        edited_t = Thread.objects.get(pk=t.id)
        eq_("new title", edited_t.title)

    def test_disallowed_404(self):
        """If document.allow_discussion is false, should return 404."""
        u = UserFactory()
        self.client.login(username=u.username, password="testpass")
        doc = DocumentFactory(allow_discussion=False)

        def check(url):
            response = get(self.client, url, args=[doc.slug])
            st = response.status_code
            eq_(404, st, "%s was %s, not 404" % (url, st))

        check("wiki.discuss.threads")
        check("wiki.discuss.new_thread")
        check("wiki.discuss.threads.feed")


class ThreadPermissionsTests(KBForumTestCase):
    def setUp(self):
        super(ThreadPermissionsTests, self).setUp()
        self.doc = DocumentFactory()
        self.u = UserFactory()
        self.thread = ThreadFactory(document=self.doc, creator=self.u)
        self.post = self.thread.new_post(creator=self.thread.creator, content="foo")
        # Login for testing 403s
        u2 = UserFactory()
        self.client.login(username=u2.username, password="testpass")

    def tearDown(self):
        self.client.logout()
        super(ThreadPermissionsTests, self).tearDown()

    def test_edit_thread_403(self):
        """Editing a thread without permissions returns 403."""
        response = get(
            self.client, "wiki.discuss.edit_thread", args=[self.doc.slug, self.thread.id]
        )
        eq_(403, response.status_code)

    def test_edit_locked_thread_403(self):
        """Editing a locked thread returns 403."""
        t = ThreadFactory(document=self.doc, creator=self.u, is_locked=True)
        response = get(self.client, "wiki.discuss.edit_thread", args=[self.doc.slug, t.id])
        eq_(403, response.status_code)

    def test_delete_thread_403(self):
        """Deleting a thread without permissions returns 403."""
        response = get(
            self.client, "wiki.discuss.delete_thread", args=[self.doc.slug, self.thread.id]
        )
        eq_(403, response.status_code)

    def test_sticky_thread_405(self):
        """Marking a thread sticky with a HTTP GET returns 405."""
        response = get(
            self.client, "wiki.discuss.sticky_thread", args=[self.doc.slug, self.thread.id]
        )
        eq_(405, response.status_code)

    def test_sticky_thread_403(self):
        """Marking a thread sticky without permissions returns 403."""
        response = post(
            self.client, "wiki.discuss.sticky_thread", args=[self.doc.slug, self.thread.id]
        )
        eq_(403, response.status_code)

    def test_locked_thread_403(self):
        """Marking a thread locked without permissions returns 403."""
        response = post(
            self.client, "wiki.discuss.lock_thread", args=[self.doc.slug, self.thread.id]
        )
        eq_(403, response.status_code)

    def test_locked_thread_405(self):
        """Marking a thread locked via a GET instead of a POST request."""
        response = get(
            self.client, "wiki.discuss.lock_thread", args=[self.doc.slug, self.thread.id]
        )
        eq_(405, response.status_code)

    def test_post_edit_403(self):
        """Editing a post without permissions returns 403."""
        response = get(
            self.client,
            "wiki.discuss.edit_post",
            args=[self.doc.slug, self.thread.id, self.post.id],
        )
        eq_(403, response.status_code)

    def test_post_delete_403(self):
        """Deleting a post without permissions returns 403."""
        response = get(
            self.client,
            "wiki.discuss.delete_post",
            args=[self.doc.slug, self.thread.id, self.post.id],
        )
        eq_(403, response.status_code)
