from django.conf import settings
from guardian.shortcuts import assign_perm

from kitsune.forums.models import Post
from kitsune.forums.tests import ForumFactory, ForumTestCase, PostFactory, ThreadFactory
from kitsune.sumo.tests import SumoPyQuery as pq
from kitsune.sumo.tests import get, post
from kitsune.users.tests import GroupFactory, UserFactory


class PostsTemplateTests(ForumTestCase):
    def test_empty_reply_errors(self):
        """Posting an empty reply shows errors."""
        u = UserFactory()
        t = ThreadFactory()

        self.client.login(username=u.username, password="testpass")
        response = post(self.client, "forums.reply", {"content": ""}, args=[t.forum.slug, t.id])

        doc = pq(response.content)
        error_msg = doc("ul.errorlist li a")[0]
        self.assertEqual(error_msg.text, "Please provide a message.")

    def test_edit_post_errors(self):
        """Changing post content works."""
        p = PostFactory()
        t = p.thread
        u = p.author

        self.client.login(username=u.username, password="testpass")
        response = post(
            self.client,
            "forums.edit_post",
            {"content": "wha?"},
            args=[t.forum.slug, t.id, p.id],
        )

        doc = pq(response.content)
        errors = doc("ul.errorlist li a")
        self.assertEqual(
            errors[0].text,
            "Your message is too short (4 characters). " + "It must be at least 5 characters.",
        )

    def test_edit_thread_template(self):
        """The edit-post template should render."""
        p = PostFactory()
        u = p.author

        self.client.login(username=u.username, password="testpass")
        res = get(
            self.client,
            "forums.edit_post",
            args=[p.thread.forum.slug, p.thread.id, p.id],
        )

        doc = pq(res.content)
        self.assertEqual(len(doc("form.edit-post")), 1)

    def test_edit_post(self):
        """Changing post content works."""
        p = PostFactory()
        t = p.thread
        u = p.author

        self.client.login(username=u.username, password="testpass")
        post(
            self.client,
            "forums.edit_post",
            {"content": "Some new content"},
            args=[t.forum.slug, t.id, p.id],
        )
        edited_p = Post.objects.get(id=p.id)

        self.assertEqual("Some new content", edited_p.content)

    def test_posts_fr(self):
        """Posts render for [fr] locale."""
        t = ThreadFactory()

        response = get(self.client, "forums.posts", args=[t.forum.slug, t.id], locale="fr")
        self.assertEqual(200, response.status_code)
        self.assertEqual(
            "{c}/fr/forums/{f}/{t}".format(c=settings.CANONICAL_URL, f=t.forum.slug, t=t.id),
            pq(response.content)('link[rel="canonical"]')[0].attrib["href"],
        )

    # TODO: This test should be enabled once the responsive redesign milestone is complete.
    # def test_long_title_truncated_in_crumbs(self):
    # """A very long thread title gets truncated in the breadcrumbs"""
    # t = ThreadFactory(title="A thread with a very very very very long title")
    # PostFactory(thread=t)
    #
    # response = get(self.client, "forums.posts", args=[t.forum.slug, t.id])
    # doc = pq(response.content)
    # crumb = doc("#breadcrumbs li:last-child")
    # self.assertEqual(crumb.text(), "A thread with a very very very very...")

    def test_edit_post_moderator(self):
        """Editing post as a moderator works."""
        p = PostFactory()
        t = p.thread
        f = t.forum

        # Create a moderator group, and give the group the edit permission.
        moderator = UserFactory()
        moderator_group = GroupFactory()
        moderator_group.user_set.add(moderator)
        assign_perm("forums.edit_forum_thread_post", moderator_group, f)

        self.client.login(username=moderator.username, password="testpass")

        r = post(
            self.client,
            "forums.edit_post",
            {"content": "More new content"},
            args=[f.slug, t.id, p.id],
        )
        self.assertEqual(200, r.status_code)

        edited_p = Post.objects.get(pk=p.pk)
        self.assertEqual("More new content", edited_p.content)

    def test_preview_reply(self):
        """Preview a reply."""
        t = ThreadFactory()
        u = t.creator

        content = "Full of awesome."
        self.client.login(username=u.username, password="testpass")
        response = post(
            self.client,
            "forums.reply",
            {"content": content, "preview": "any string"},
            args=[t.forum.slug, t.id],
        )
        self.assertEqual(200, response.status_code)
        doc = pq(response.content)
        self.assertEqual(content, doc("#post-preview div.content").text())
        self.assertEqual(1, t.post_set.count())

    def test_watch_thread(self):
        """Watch and unwatch a thread."""
        t = ThreadFactory()
        u = UserFactory()

        self.client.login(username=u.username, password="testpass")

        response = post(
            self.client,
            "forums.watch_thread",
            {"watch": "yes"},
            args=[t.forum.slug, t.id],
        )
        self.assertContains(response, "Stop watching this thread")

        response = post(
            self.client,
            "forums.watch_thread",
            {"watch": "no"},
            args=[t.forum.slug, t.id],
        )
        self.assertNotContains(response, "Stop watching this thread")

    def test_show_reply_fields(self):
        """Reply fields show if user has permission to post."""
        t = ThreadFactory()
        u = UserFactory()

        self.client.login(username=u.username, password="testpass")
        response = get(self.client, "forums.posts", args=[t.forum.slug, t.pk])
        self.assertContains(response, "thread-reply")

    def test_restricted_hide_reply(self):
        """Reply fields don't show if user has no permission to post."""
        f = ForumFactory(restrict_posting=True)
        t = ThreadFactory(forum=f)
        u = UserFactory()
        self.client.login(username=u.username, password="testpass")
        response = get(self.client, "forums.posts", args=[f.slug, t.pk])
        self.assertNotContains(response, "thread-reply")

    def test_links_nofollow(self):
        """Links posted should have rel=nofollow."""
        p = PostFactory(content="linking http://test.org")
        t = p.thread
        f = t.forum

        response = get(self.client, "forums.posts", args=[f.slug, t.pk])
        doc = pq(response.content)
        self.assertEqual("nofollow", doc("ol.posts div.content a")[0].attrib["rel"])

    def test_num_replies(self):
        """Verify the number of replies label."""
        t = ThreadFactory()

        response = get(self.client, "forums.posts", args=[t.forum.slug, t.id])
        self.assertEqual(200, response.status_code)
        assert b"0 Replies" in response.content

        PostFactory(thread=t)
        PostFactory(thread=t)

        response = get(self.client, "forums.posts", args=[t.forum.slug, t.id])
        self.assertEqual(200, response.status_code)
        assert b"2 Replies" in response.content

    def test_num_posts(self):
        """Verify the number of posts in all threads for a given post's author."""
        t = ThreadFactory()

        response = get(self.client, "forums.posts", args=[t.forum.slug, t.id])
        self.assertEqual(200, response.status_code)
        self.assertIn(b"1 post", response.content)

        ThreadFactory(creator=t.creator)
        ThreadFactory(creator=t.creator)

        response = get(self.client, "forums.posts", args=[t.forum.slug, t.id])
        self.assertEqual(200, response.status_code)
        self.assertIn(b"3 posts", response.content)

    def test_youtube_in_post(self):
        """Verify youtube video embedding."""
        u = UserFactory()
        t = ThreadFactory()

        self.client.login(username=u.username, password="testpass")
        response = post(
            self.client,
            "forums.reply",
            {"content": "[[V:http://www.youtube.com/watch?v=oHg5SJYRHA0]]"},
            args=[t.forum.slug, t.id],
        )

        doc = pq(response.content)
        assert doc("iframe")[0].attrib["src"].startswith("//www.youtube.com/embed/oHg5SJYRHA0")


class ThreadsTemplateTests(ForumTestCase):
    def test_last_thread_post_link_has_post_id(self):
        """Make sure the last post url links to the last post (#post-<id>)."""
        t = ThreadFactory()
        last = PostFactory(thread=t)

        response = get(self.client, "forums.threads", args=[t.forum.slug])
        doc = pq(response.content)
        last_post_link = doc(".threads .last-post a:not(.username)")[0]
        href = last_post_link.attrib["href"]
        self.assertEqual(href.split("#")[1], "post-%s" % last.id)

    def test_empty_thread_errors(self):
        """Posting an empty thread shows errors."""
        f = ForumFactory()
        u = UserFactory()

        self.client.login(username=u.username, password="testpass")
        response = post(
            self.client,
            "forums.new_thread",
            {"title": "", "content": ""},
            args=[f.slug],
        )
        doc = pq(response.content)
        errors = doc("ul.errorlist li a")
        self.assertEqual(errors[0].text, "Please provide a title.")
        self.assertEqual(errors[1].text, "Please provide a message.")

    def test_new_short_thread_errors(self):
        """Posting a short new thread shows errors."""
        f = ForumFactory()
        u = UserFactory()

        self.client.login(username=u.username, password="testpass")
        response = post(
            self.client,
            "forums.new_thread",
            {"title": "wha?", "content": "wha?"},
            args=[f.slug],
        )

        doc = pq(response.content)
        errors = doc("ul.errorlist li a")
        self.assertEqual(
            errors[0].text,
            "Your title is too short (4 characters). " + "It must be at least 5 characters.",
        )
        self.assertEqual(
            errors[1].text,
            "Your message is too short (4 characters). " + "It must be at least 5 characters.",
        )

    def test_edit_thread_errors(self):
        """Editing thread with too short of a title shows errors."""
        t = ThreadFactory()
        creator = t.creator

        self.client.login(username=creator.username, password="testpass")
        response = post(
            self.client,
            "forums.edit_thread",
            {"title": "wha?"},
            args=[t.forum.slug, t.id],
        )

        doc = pq(response.content)
        errors = doc("ul.errorlist li a")
        self.assertEqual(
            errors[0].text,
            "Your title is too short (4 characters). " + "It must be at least 5 characters.",
        )

    def test_edit_thread_template(self):
        """The edit-thread template should render."""
        t = ThreadFactory()
        creator = t.creator

        self.client.login(username=creator.username, password="testpass")
        res = get(self.client, "forums.edit_thread", args=[t.forum.slug, t.id])

        doc = pq(res.content)
        self.assertEqual(len(doc("form.edit-thread")), 1)

    def test_watch_forum(self):
        """Watch and unwatch a forum."""
        f = ForumFactory()
        u = UserFactory()

        self.client.login(username=u.username, password="testpass")

        response = post(self.client, "forums.watch_forum", {"watch": "yes"}, args=[f.slug])
        self.assertContains(response, "Stop watching this forum")

        response = post(self.client, "forums.watch_forum", {"watch": "no"}, args=[f.slug])
        self.assertNotContains(response, "Stop watching this forum")

    def test_canonical_url(self):
        """Verify the canonical URL is set correctly."""
        f = ForumFactory()

        response = get(self.client, "forums.threads", args=[f.slug])
        self.assertEqual(
            "%s/en-US/forums/%s/" % (settings.CANONICAL_URL, f.slug),
            pq(response.content)('link[rel="canonical"]')[0].attrib["href"],
        )

    def test_show_new_thread(self):
        """'Post new thread' shows if user has permission to post."""
        f = ForumFactory()
        u = UserFactory()

        self.client.login(username=u.username, password="testpass")
        response = get(self.client, "forums.threads", args=[f.slug])
        self.assertContains(response, "Post a new thread")

    def test_restricted_hide_new_thread(self):
        """'Post new thread' doesn't show if user has no permission to post."""
        f = ForumFactory(restrict_posting=True)
        u = UserFactory()
        self.client.login(username=u.username, password="testpass")
        response = get(self.client, "forums.threads", args=[f.slug])
        self.assertNotContains(response, "Post a new thread")


class ForumsTemplateTests(ForumTestCase):
    def test_last_post_link_has_post_id(self):
        """Make sure the last post url links to the last post (#post-<id>)."""
        p = PostFactory()

        response = get(self.client, "forums.forums")
        doc = pq(response.content)
        last_post_link = doc(".forums .last-post a:not(.username)")[0]
        href = last_post_link.attrib["href"]
        self.assertEqual(href.split("#")[1], "post-%s" % p.id)

    def test_restricted_is_invisible(self):
        """Forums with restricted view_in permission shouldn't show up."""
        restricted_forum = ForumFactory(restrict_viewing=True)
        response = get(self.client, "forums.forums")
        self.assertNotContains(response, restricted_forum.slug)

    def test_canonical_url(self):
        response = get(self.client, "forums.forums")
        self.assertEqual(
            "{}/en-US/forums/".format(settings.CANONICAL_URL),
            pq(response.content)('link[rel="canonical"]')[0].attrib["href"],
        )

    def test_display_order(self):
        """Verify the display_order is respected."""
        forum1 = ForumFactory(display_order=1)
        forum2 = ForumFactory(display_order=2)

        # forum1 should be listed first
        r = get(self.client, "forums.forums")
        self.assertEqual(200, r.status_code)
        doc = pq(r.content)
        self.assertEqual(forum1.name, doc(".forums tr a").first().text())

        forum1.display_order = 3
        forum1.save()

        # forum2 should be listed first
        r = get(self.client, "forums.forums")
        self.assertEqual(200, r.status_code)
        doc = pq(r.content)
        self.assertEqual(forum2.name, doc(".forums tr a").first().text())

    def test_is_listed(self):
        """Verify is_listed is respected."""
        forum1 = ForumFactory(is_listed=True)
        forum2 = ForumFactory(is_listed=True)

        # Both forums should be listed.
        r = get(self.client, "forums.forums")
        self.assertEqual(200, r.status_code)
        doc = pq(r.content)
        self.assertEqual(2, len(doc(".forums tr")))

        forum1.is_listed = False
        forum1.save()

        # Only forum2 should be listed.
        r = get(self.client, "forums.forums")
        self.assertEqual(200, r.status_code)
        doc = pq(r.content)
        self.assertEqual(1, len(doc(".forums tr")))
        self.assertEqual(forum2.name, doc(".forums tr a").text())

    def test_thread_counts(self):
        """Verify the thread counts."""
        forum1 = ThreadFactory().forum
        forum2 = ThreadFactory().forum
        ThreadFactory(forum=forum2)
        forum3 = ThreadFactory().forum
        ThreadFactory(forum=forum3)
        ThreadFactory(forum=forum3)

        response = get(self.client, "forums.forums")
        doc = pq(response.content)
        forum_names = doc("h5.sumo-card-heading a").text().split()
        self.assertEqual(forum_names, [forum1.name, forum2.name, forum3.name])
        forum_thread_counts = doc("td.threads").text().split()
        self.assertEqual(forum_thread_counts, ["1", "2", "3"])


class NewThreadTemplateTests(ForumTestCase):
    def test_preview(self):
        """Preview the thread post."""
        f = ForumFactory()
        u = UserFactory()

        self.client.login(username=u.username, password="testpass")
        content = "Full of awesome."
        response = post(
            self.client,
            "forums.new_thread",
            {"title": "Topic", "content": content, "preview": "any string"},
            args=[f.slug],
        )
        self.assertEqual(200, response.status_code)
        doc = pq(response.content)
        self.assertEqual(content, doc("#post-preview div.content").text())
        self.assertEqual(0, f.thread_set.count())  # No thread was created.
