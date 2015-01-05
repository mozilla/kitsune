from django.contrib.contenttypes.models import ContentType

from nose.tools import eq_
from pyquery import PyQuery as pq

from kitsune.access.tests import permission
from kitsune.forums.models import Post
from kitsune.forums.tests import (
    ForumTestCase, forum, thread, post as forum_post)
from kitsune.sumo.tests import get, post
from kitsune.users.tests import user, group


class PostsTemplateTests(ForumTestCase):

    def test_empty_reply_errors(self):
        """Posting an empty reply shows errors."""
        u = user(save=True)
        t = forum_post(save=True).thread

        self.client.login(username=u.username, password='testpass')
        response = post(self.client, 'forums.reply', {'content': ''},
                        args=[t.forum.slug, t.id])

        doc = pq(response.content)
        error_msg = doc('ul.errorlist li a')[0]
        eq_(error_msg.text, 'Please provide a message.')

    def test_edit_post_errors(self):
        """Changing post content works."""
        p = forum_post(save=True)
        t = p.thread
        u = p.author

        self.client.login(username=u.username, password='testpass')
        response = post(self.client, 'forums.edit_post',
                        {'content': 'wha?'}, args=[t.forum.slug, t.id, p.id])

        doc = pq(response.content)
        errors = doc('ul.errorlist li a')
        eq_(errors[0].text,
            'Your message is too short (4 characters). ' +
            'It must be at least 5 characters.')

    def test_edit_thread_template(self):
        """The edit-post template should render."""
        p = forum_post(save=True)
        u = p.author

        self.client.login(username=u.username, password='testpass')
        res = get(self.client, 'forums.edit_post',
                  args=[p.thread.forum.slug, p.thread.id, p.id])

        doc = pq(res.content)
        eq_(len(doc('form.edit-post')), 1)

    def test_edit_post(self):
        """Changing post content works."""
        p = forum_post(save=True)
        t = p.thread
        u = p.author

        self.client.login(username=u.username, password='testpass')
        post(self.client, 'forums.edit_post', {'content': 'Some new content'},
             args=[t.forum.slug, t.id, p.id])
        edited_p = Post.objects.get(id=p.id)

        eq_('Some new content', edited_p.content)

    def test_posts_fr(self):
        """Posts render for [fr] locale."""
        t = forum_post(save=True).thread

        response = get(self.client, 'forums.posts', args=[t.forum.slug, t.id],
                       locale='fr')
        eq_(200, response.status_code)
        eq_('/forums/{f}/{t}'.format(f=t.forum.slug, t=t.id),
            pq(response.content)('link[rel="canonical"]')[0].attrib['href'])

    def test_long_title_truncated_in_crumbs(self):
        """A very long thread title gets truncated in the breadcrumbs"""
        t = thread(title='A thread with a very very long title', save=True)
        forum_post(thread=t, save=True)

        response = get(self.client, 'forums.posts', args=[t.forum.slug, t.id])
        doc = pq(response.content)
        crumb = doc('#breadcrumbs li:last-child')
        eq_(crumb.text(), 'A thread with a very very ...')

    def test_edit_post_moderator(self):
        """Editing post as a moderator works."""
        p = forum_post(save=True)
        t = p.thread
        f = t.forum

        # Create the moderator group, give it the edit permission
        # and add a moderator.
        moderator_group = group(save=True)
        ct = ContentType.objects.get_for_model(f)
        permission(codename='forums_forum.post_edit_forum', content_type=ct,
                   object_id=f.id, group=moderator_group, save=True)
        moderator = user(save=True)
        moderator_group.user_set.add(moderator)

        self.client.login(username=moderator.username, password='testpass')

        r = post(self.client, 'forums.edit_post',
                 {'content': 'More new content'}, args=[f.slug, t.id, p.id])
        eq_(200, r.status_code)

        edited_p = Post.uncached.get(pk=p.pk)
        eq_('More new content', edited_p.content)

    def test_preview_reply(self):
        """Preview a reply."""
        t = forum_post(save=True).thread
        u = t.creator

        content = 'Full of awesome.'
        self.client.login(username=u.username, password='testpass')
        response = post(self.client, 'forums.reply',
                        {'content': content, 'preview': 'any string'},
                        args=[t.forum.slug, t.id])
        eq_(200, response.status_code)
        doc = pq(response.content)
        eq_(content, doc('#post-preview div.content').text())
        eq_(1, t.post_set.count())

    def test_watch_thread(self):
        """Watch and unwatch a thread."""
        t = forum_post(save=True).thread
        u = user(save=True)

        self.client.login(username=u.username, password='testpass')

        response = post(self.client, 'forums.watch_thread', {'watch': 'yes'},
                        args=[t.forum.slug, t.id])
        self.assertContains(response, 'Stop watching this thread')

        response = post(self.client, 'forums.watch_thread', {'watch': 'no'},
                        args=[t.forum.slug, t.id])
        self.assertNotContains(response, 'Stop watching this thread')

    def test_show_reply_fields(self):
        """Reply fields show if user has permission to post."""
        t = forum_post(save=True).thread
        u = user(save=True)

        self.client.login(username=u.username, password='testpass')
        response = get(self.client, 'forums.posts', args=[t.forum.slug, t.pk])
        self.assertContains(response, 'thread-reply')

    def test_restricted_hide_reply(self):
        """Reply fields don't show if user has no permission to post."""
        t = forum_post(save=True).thread
        f = t.forum
        ct = ContentType.objects.get_for_model(f)
        # If the forum has the permission and the user isn't assigned said
        # permission, then they can't post.
        permission(codename='forums_forum.post_in_forum', content_type=ct,
                   object_id=f.id, save=True)
        u = user(save=True)

        self.client.login(username=u.username, password='testpass')
        response = get(self.client, 'forums.posts', args=[f.slug, t.pk])
        self.assertNotContains(response, 'thread-reply')

    def test_links_nofollow(self):
        """Links posted should have rel=nofollow."""
        p = forum_post(content='linking http://test.org', save=True)
        t = p.thread
        f = t.forum

        response = get(self.client, 'forums.posts', args=[f.slug, t.pk])
        doc = pq(response.content)
        eq_('nofollow', doc('ol.posts div.content a')[0].attrib['rel'])

    def test_num_replies(self):
        """Verify the number of replies label."""
        t = forum_post(save=True).thread

        response = get(self.client, 'forums.posts', args=[t.forum.slug, t.id])
        eq_(200, response.status_code)
        assert '0 Replies' in response.content

        forum_post(thread=t, save=True)
        forum_post(thread=t, save=True)

        response = get(self.client, 'forums.posts', args=[t.forum.slug, t.id])
        eq_(200, response.status_code)
        assert '2 Replies' in response.content

    def test_youtube_in_post(self):
        """Verify youtube video embedding."""
        u = user(save=True)
        t = forum_post(save=True).thread

        self.client.login(username=u.username, password='testpass')
        response = post(
            self.client,
            'forums.reply',
            {'content': '[[V:http://www.youtube.com/watch?v=oHg5SJYRHA0]]'},
            args=[t.forum.slug, t.id])

        doc = pq(response.content)
        assert doc('iframe')[0].attrib['src'].startswith(
            '//www.youtube.com/embed/oHg5SJYRHA0')


class ThreadsTemplateTests(ForumTestCase):

    def test_last_thread_post_link_has_post_id(self):
        """Make sure the last post url links to the last post (#post-<id>).
        """
        t = forum_post(save=True).thread
        last = forum_post(thread=t, save=True)

        response = get(self.client, 'forums.threads', args=[t.forum.slug])
        doc = pq(response.content)
        last_post_link = doc('ol.threads div.last-post a:not(.username)')[0]
        href = last_post_link.attrib['href']
        eq_(href.split('#')[1], 'post-%s' % last.id)

    def test_empty_thread_errors(self):
        """Posting an empty thread shows errors."""
        f = forum(save=True)
        u = user(save=True)

        self.client.login(username=u.username, password='testpass')
        response = post(self.client, 'forums.new_thread',
                        {'title': '', 'content': ''}, args=[f.slug])
        doc = pq(response.content)
        errors = doc('ul.errorlist li a')
        eq_(errors[0].text, 'Please provide a title.')
        eq_(errors[1].text, 'Please provide a message.')

    def test_new_short_thread_errors(self):
        """Posting a short new thread shows errors."""
        f = forum(save=True)
        u = user(save=True)

        self.client.login(username=u.username, password='testpass')
        response = post(self.client, 'forums.new_thread',
                        {'title': 'wha?', 'content': 'wha?'}, args=[f.slug])

        doc = pq(response.content)
        errors = doc('ul.errorlist li a')
        eq_(errors[0].text,
            'Your title is too short (4 characters). ' +
            'It must be at least 5 characters.')
        eq_(errors[1].text,
            'Your message is too short (4 characters). ' +
            'It must be at least 5 characters.')

    def test_edit_thread_errors(self):
        """Editing thread with too short of a title shows errors."""
        t = forum_post(save=True).thread
        creator = t.creator

        self.client.login(username=creator.username, password='testpass')
        response = post(self.client, 'forums.edit_thread',
                        {'title': 'wha?'}, args=[t.forum.slug, t.id])

        doc = pq(response.content)
        errors = doc('ul.errorlist li a')
        eq_(errors[0].text,
            'Your title is too short (4 characters). ' +
            'It must be at least 5 characters.')

    def test_edit_thread_template(self):
        """The edit-thread template should render."""
        t = forum_post(save=True).thread
        creator = t.creator

        self.client.login(username=creator.username, password='testpass')
        res = get(self.client, 'forums.edit_thread',
                  args=[t.forum.slug, t.id])

        doc = pq(res.content)
        eq_(len(doc('form.edit-thread')), 1)

    def test_watch_forum(self):
        """Watch and unwatch a forum."""
        f = forum(save=True)
        u = user(save=True)

        self.client.login(username=u.username, password='testpass')

        response = post(self.client, 'forums.watch_forum', {'watch': 'yes'},
                        args=[f.slug])
        self.assertContains(response, 'Stop watching this forum')

        response = post(self.client, 'forums.watch_forum', {'watch': 'no'},
                        args=[f.slug])
        self.assertNotContains(response, 'Stop watching this forum')

    def test_canonical_url(self):
        """Verify the canonical URL is set correctly."""
        f = forum(save=True)

        response = get(self.client, 'forums.threads', args=[f.slug])
        eq_('/forums/%s' % f.slug,
            pq(response.content)('link[rel="canonical"]')[0].attrib['href'])

    def test_show_new_thread(self):
        """'Post new thread' shows if user has permission to post."""
        f = forum(save=True)
        u = user(save=True)

        self.client.login(username=u.username, password='testpass')
        response = get(self.client, 'forums.threads', args=[f.slug])
        self.assertContains(response, 'Post a new thread')

    def test_restricted_hide_new_thread(self):
        """'Post new thread' doesn't show if user has no permission to post.
        """
        f = forum(save=True)
        ct = ContentType.objects.get_for_model(f)
        # If the forum has the permission and the user isn't assigned said
        # permission, then they can't post.
        permission(codename='forums_forum.post_in_forum', content_type=ct,
                   object_id=f.id, save=True)
        u = user(save=True)

        self.client.login(username=u.username, password='testpass')
        response = get(self.client, 'forums.threads', args=[f.slug])
        self.assertNotContains(response, 'Post a new thread')


class ForumsTemplateTests(ForumTestCase):

    def test_last_post_link_has_post_id(self):
        """Make sure the last post url links to the last post (#post-<id>).
        """
        p = forum_post(save=True)

        response = get(self.client, 'forums.forums')
        doc = pq(response.content)
        last_post_link = doc('ol.forums div.last-post a:not(.username)')[0]
        href = last_post_link.attrib['href']
        eq_(href.split('#')[1], 'post-%s' % p.id)

    def test_restricted_is_invisible(self):
        """Forums with restricted view_in permission shouldn't show up."""
        restricted_forum = forum(save=True)
        # Make it restricted.
        ct = ContentType.objects.get_for_model(restricted_forum)
        permission(codename='forums_forum.view_in_forum', content_type=ct,
                   object_id=restricted_forum.id, save=True)

        response = get(self.client, 'forums.forums')
        self.assertNotContains(response, restricted_forum.slug)

    def test_canonical_url(self):
        response = get(self.client, 'forums.forums')
        eq_('/forums',
            pq(response.content)('link[rel="canonical"]')[0].attrib['href'])

    def test_display_order(self):
        """Verify the display_order is respected."""
        forum1 = forum(display_order=1, save=True)
        forum2 = forum(display_order=2, save=True)

        # forum1 should be listed first
        r = get(self.client, 'forums.forums')
        eq_(200, r.status_code)
        doc = pq(r.content)
        eq_(forum1.name, doc('ol.forums > li a:first').text())

        forum1.display_order = 3
        forum1.save()

        # forum2 should be listed first
        r = get(self.client, 'forums.forums')
        eq_(200, r.status_code)
        doc = pq(r.content)
        eq_(forum2.name, doc('ol.forums > li a:first').text())

    def test_is_listed(self):
        """Verify is_listed is respected."""
        forum1 = forum(is_listed=True, save=True)
        forum2 = forum(is_listed=True, save=True)

        # Both forums should be listed.
        r = get(self.client, 'forums.forums')
        eq_(200, r.status_code)
        doc = pq(r.content)
        eq_(2, len(doc('ol.forums > li')))

        forum1.is_listed = False
        forum1.save()

        # Only forum2 should be listed.
        r = get(self.client, 'forums.forums')
        eq_(200, r.status_code)
        doc = pq(r.content)
        eq_(1, len(doc('ol.forums > li')))
        eq_(forum2.name, doc('ol.forums > li a').text())


class NewThreadTemplateTests(ForumTestCase):
    def test_preview(self):
        """Preview the thread post."""
        f = forum(save=True)
        u = user(save=True)

        self.client.login(username=u.username, password='testpass')
        content = 'Full of awesome.'
        response = post(self.client, 'forums.new_thread',
                        {'title': 'Topic', 'content': content,
                         'preview': 'any string'}, args=[f.slug])
        eq_(200, response.status_code)
        doc = pq(response.content)
        eq_(content, doc('#post-preview div.content').text())
        eq_(0, f.thread_set.count())  # No thread was created.
