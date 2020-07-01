import time

from nose.tools import eq_
from pyquery import PyQuery as pq

from kitsune.flagit.models import FlaggedObject
from kitsune.kbforums.models import Post
from kitsune.kbforums.models import Thread
from kitsune.kbforums.tests import KBForumTestCase
from kitsune.kbforums.tests import PostFactory
from kitsune.kbforums.tests import ThreadFactory
from kitsune.sumo.tests import get
from kitsune.sumo.tests import post
from kitsune.sumo.urlresolvers import reverse
from kitsune.users.tests import add_permission
from kitsune.users.tests import UserFactory
from kitsune.wiki.tests import ApprovedRevisionFactory
from kitsune.wiki.tests import DocumentFactory


class PostsTemplateTests(KBForumTestCase):
    def test_empty_reply_errors(self):
        """Posting an empty reply shows errors."""
        u = UserFactory()
        self.client.login(username=u.username, password="testpass")

        d = DocumentFactory()
        t = ThreadFactory(document=d)
        response = post(
            self.client, "wiki.discuss.reply", {"content": ""}, args=[d.slug, t.id]
        )

        doc = pq(response.content)
        error_msg = doc("ul.errorlist li a")[0]
        eq_(error_msg.text, "Please provide a message.")

    def test_edit_post_errors(self):
        """Changing post content works."""
        u = UserFactory()
        self.client.login(username=u.username, password="testpass")

        t = ThreadFactory(creator=u, is_locked=False)
        p = t.new_post(creator=u, content="foo")
        response = post(
            self.client,
            "wiki.discuss.edit_post",
            {"content": "wha?"},
            args=[t.document.slug, t.id, p.id],
        )

        doc = pq(response.content)
        errors = doc("ul.errorlist li a")
        eq_(
            errors[0].text,
            "Your message is too short (4 characters). "
            + "It must be at least 5 characters.",
        )

    def test_edit_thread_template(self):
        """The edit-post template should render."""
        u = UserFactory()
        self.client.login(username=u.username, password="testpass")

        t = ThreadFactory(creator=u, is_locked=False)
        p = t.new_post(creator=u, content="foo")
        res = get(
            self.client,
            "wiki.discuss.edit_post",
            args=[p.thread.document.slug, p.thread.id, p.id],
        )

        doc = pq(res.content)
        eq_(len(doc("form.edit-post")), 1)

    def test_edit_post(self):
        """Changing post content works."""
        u = UserFactory()
        self.client.login(username=u.username, password="testpass")

        d = DocumentFactory()
        t = ThreadFactory(document=d)
        p = t.new_post(creator=u, content="foo")
        post(
            self.client,
            "wiki.discuss.edit_post",
            {"content": "Some new content"},
            args=[d.slug, t.id, p.id],
        )
        edited_p = t.post_set.get(pk=p.id)

        eq_("Some new content", edited_p.content)

    # TODO: This test should be enabled once the responsive redesign milestone is complete.
    # def test_long_title_truncated_in_crumbs(self):
    # """A very long thread title gets truncated in the breadcrumbs"""
    # d = DocumentFactory()
    # t = ThreadFactory(title='A thread with a very very very very very' * 5, document=d)
    # response = get(self.client, 'wiki.discuss.posts', args=[d.slug, t.id])
    # doc = pq(response.content)
    # crumb = doc('#breadcrumbs li:last-child')
    # eq_(crumb.text(), 'A thread with a very very very very...')

    def test_edit_post_moderator(self):
        """Editing post as a moderator works."""
        u = UserFactory()
        add_permission(u, Post, "change_post")
        self.client.login(username=u.username, password="testpass")

        p = PostFactory()
        t = p.thread
        d = t.document

        r = post(
            self.client,
            "wiki.discuss.edit_post",
            {"content": "More new content"},
            args=[d.slug, t.id, p.id],
        )
        eq_(200, r.status_code)

        edited_p = Post.objects.get(pk=p.pk)
        eq_("More new content", edited_p.content)

    def test_preview_reply(self):
        """Preview a reply."""
        u = UserFactory()
        self.client.login(username=u.username, password="testpass")

        d = DocumentFactory()
        t = ThreadFactory(document=d)
        num_posts = t.post_set.count()
        content = "Full of awesome."
        response = post(
            self.client,
            "wiki.discuss.reply",
            {"content": content, "preview": "any string"},
            args=[d.slug, t.id],
        )
        eq_(200, response.status_code)
        doc = pq(response.content)
        eq_(content, doc("#post-preview div.content").text())
        eq_(num_posts, t.post_set.count())

    def test_preview_async(self):
        """Preview a reply."""
        u = UserFactory()
        self.client.login(username=u.username, password="testpass")

        d = DocumentFactory()
        content = "Full of awesome."
        response = post(
            self.client,
            "wiki.discuss.post_preview_async",
            {"content": content},
            args=[d.slug],
        )
        eq_(200, response.status_code)
        doc = pq(response.content)
        eq_(content, doc("div.content").text())

    def test_watch_thread(self):
        """Watch and unwatch a thread."""
        u = UserFactory()
        self.client.login(username=u.username, password="testpass")

        t = ThreadFactory()
        response = post(
            self.client,
            "wiki.discuss.watch_thread",
            {"watch": "yes"},
            args=[t.document.slug, t.id],
        )
        self.assertContains(response, "Stop")

        response = post(
            self.client,
            "wiki.discuss.watch_thread",
            {"watch": "no"},
            args=[t.document.slug, t.id],
        )
        self.assertNotContains(response, "Stop")

    def test_links_nofollow(self):
        """Links posted should have rel=nofollow."""
        u = UserFactory()
        t = ThreadFactory()
        t.new_post(creator=u, content="linking http://test.org")
        response = get(self.client, "wiki.discuss.posts", args=[t.document.slug, t.pk])
        doc = pq(response.content)
        eq_("nofollow", doc("ol.posts div.content a")[0].attrib["rel"])


class ThreadsTemplateTests(KBForumTestCase):
    def test_last_thread_post_link_has_post_id(self):
        """Make sure the last post url links to the last post (#post-<id>)."""
        u = UserFactory()
        t = ThreadFactory()
        t.new_post(creator=u, content="foo")
        p2 = t.new_post(creator=u, content="bar")
        response = get(self.client, "wiki.discuss.threads", args=[t.document.slug])

        doc = pq(response.content)
        last_post_link = doc("tr.threads td.last-post a:not(.username)")[0]
        href = last_post_link.attrib["href"]
        eq_(href.split("#")[1], "post-%d" % p2.id)

    def test_empty_thread_errors(self):
        """Posting an empty thread shows errors."""
        u = UserFactory()
        self.client.login(username=u.username, password="testpass")

        d = DocumentFactory()
        response = post(
            self.client,
            "wiki.discuss.new_thread",
            {"title": "", "content": ""},
            args=[d.slug],
        )

        doc = pq(response.content)
        errors = doc("ul.errorlist li a")
        eq_(errors[0].text, "Please provide a title.")
        eq_(errors[1].text, "Please provide a message.")

    def test_new_short_thread_errors(self):
        """Posting a short new thread shows errors."""
        u = UserFactory()
        self.client.login(username=u.username, password="testpass")

        d = DocumentFactory()
        response = post(
            self.client,
            "wiki.discuss.new_thread",
            {"title": "wha?", "content": "wha?"},
            args=[d.slug],
        )

        doc = pq(response.content)
        errors = doc("ul.errorlist li a")
        eq_(
            errors[0].text,
            "Your title is too short (4 characters). "
            + "It must be at least 5 characters.",
        )
        eq_(
            errors[1].text,
            "Your message is too short (4 characters). "
            + "It must be at least 5 characters.",
        )

    def test_edit_thread_errors(self):
        """Editing thread with too short of a title shows errors."""
        u = UserFactory()
        self.client.login(username=u.username, password="testpass")

        d = DocumentFactory()
        t = ThreadFactory(document=d, creator=u)
        response = post(
            self.client,
            "wiki.discuss.edit_thread",
            {"title": "wha?"},
            args=[d.slug, t.id],
        )

        doc = pq(response.content)
        errors = doc("ul.errorlist li a")
        eq_(
            errors[0].text,
            "Your title is too short (4 characters). "
            + "It must be at least 5 characters.",
        )

    def test_edit_thread_template(self):
        """The edit-thread template should render."""
        u = UserFactory()
        self.client.login(username=u.username, password="testpass")

        t = ThreadFactory(creator=u, is_locked=False)
        res = get(self.client, "wiki.discuss.edit_thread", args=[t.document.slug, t.id])

        doc = pq(res.content)
        eq_(len(doc("form.edit-thread")), 1)

    def test_watch_forum(self):
        """Watch and unwatch a forum."""
        u = UserFactory()
        self.client.login(username=u.username, password="testpass")

        d = DocumentFactory()
        response = post(
            self.client, "wiki.discuss.watch_forum", {"watch": "yes"}, args=[d.slug]
        )
        self.assertContains(response, "Stop")

        response = post(
            self.client, "wiki.discuss.watch_forum", {"watch": "no"}, args=[d.slug]
        )
        self.assertNotContains(response, "Stop")

    def test_watch_locale(self):
        """Watch and unwatch a locale."""
        u = UserFactory()
        self.client.login(username=u.username, password="testpass")

        d = DocumentFactory()
        next_url = reverse("wiki.discuss.threads", args=[d.slug])
        response = post(
            self.client, "wiki.discuss.watch_locale", {"watch": "yes", "next": next_url}
        )
        self.assertContains(response, "Turn off emails")

        response = post(
            self.client, "wiki.discuss.watch_locale", {"watch": "no", "next": next_url}
        )
        self.assertContains(response, "Get emailed when there is new discussion")

    def test_orphan_non_english(self):
        """Discussing a non-English article with no parent shouldn't crash."""
        # Guard against regressions of bug 658045.
        r = ApprovedRevisionFactory(document__locale="de")
        response = self.client.get(
            reverse("wiki.discuss.threads", args=[r.document.slug], locale="de")
        )
        eq_(200, response.status_code)

    def test_all_locale_discussions(self):
        """Start or stop watching all discussions in a locale."""
        u = UserFactory()
        self.client.login(username=u.username, password="testpass")
        next_url = reverse("wiki.locale_discussions")
        # Watch locale.
        response = post(
            self.client, "wiki.discuss.watch_locale", {"watch": "yes", "next": next_url}
        )
        self.assertContains(response, "Stop watching this locale")
        # Stop watching locale.
        response = post(
            self.client, "wiki.discuss.watch_locale", {"watch": "no", "next": next_url}
        )
        self.assertContains(response, "Watch this locale")

    def test_locale_discussions_ignores_sticky(self):
        """Sticky flag is ignored in locale discussions view"""
        u = UserFactory()
        d = DocumentFactory()
        t = ThreadFactory(title="Sticky Thread", is_sticky=True, document=d)
        t.new_post(creator=u, content="foo")
        t2 = ThreadFactory(
            title="A thread with a very very long", is_sticky=False, document=d
        )
        t2.new_post(creator=u, content="bar")
        time.sleep(1)
        t2.new_post(creator=u, content="last")
        self.client.login(username=u.username, password="testpass")
        response = post(self.client, "wiki.locale_discussions")
        eq_(200, response.status_code)
        doc = pq(response.content)
        title = doc(".threads .title a:first").text()
        assert title.startswith("A thread with a very very long")


class NewThreadTemplateTests(KBForumTestCase):
    def test_preview(self):
        """Preview the thread post."""
        u = UserFactory()
        self.client.login(username=u.username, password="testpass")
        d = DocumentFactory()
        num_threads = d.thread_set.count()
        content = "Full of awesome."
        response = post(
            self.client,
            "wiki.discuss.new_thread",
            {"title": "Topic", "content": content, "preview": "any string"},
            args=[d.slug],
        )
        eq_(200, response.status_code)
        doc = pq(response.content)
        eq_(content, doc("#post-preview div.content").text())
        eq_(num_threads, d.thread_set.count())


class FlaggedPostTests(KBForumTestCase):
    def test_flag_kbforum_post(self):
        u = UserFactory()
        t = ThreadFactory()
        p = t.new_post(creator=u, content="foo")
        f = FlaggedObject(content_object=p, reason="spam", creator_id=u.id)
        f.save()
        # Make sure flagit queue page works
        u2 = UserFactory()
        add_permission(u2, FlaggedObject, "can_moderate")
        self.client.login(username=u2.username, password="testpass")
        response = get(self.client, "flagit.queue")
        eq_(200, response.status_code)
        doc = pq(response.content)
        eq_(1, len(doc("#flagged-queue li")))


class TestRatelimiting(KBForumTestCase):
    def test_post_ratelimit(self):
        """Verify that rate limiting kicks in after 4 threads or replies."""
        d = DocumentFactory()
        u = UserFactory()
        self.client.login(username=u.username, password="testpass")

        # Create 2 threads:
        for i in range(2):
            response = post(
                self.client,
                "wiki.discuss.new_thread",
                {"title": "Topic", "content": "hellooo"},
                args=[d.slug],
            )
            eq_(200, response.status_code)

        # Now 3 replies (only 2 should save):
        t = Thread.objects.all()[0]
        for i in range(3):
            response = post(
                self.client,
                "wiki.discuss.reply",
                {"content": "hellooo"},
                args=[d.slug, t.id],
            )
            eq_(200, response.status_code)

        # And another thread that shouldn't save:
        response = post(
            self.client,
            "wiki.discuss.new_thread",
            {"title": "Topic", "content": "hellooo"},
            args=[d.slug],
        )

        # We should only have 4 posts (each thread and reply creates a post).
        eq_(4, Post.objects.count())
