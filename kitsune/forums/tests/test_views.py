from mock import patch, Mock
from nose.tools import eq_

from django.contrib.contenttypes.models import ContentType

from kitsune.access.tests import permission
from kitsune.forums.events import NewThreadEvent, NewPostEvent
from kitsune.forums.models import Forum, Thread
from kitsune.forums.tests import (
    ForumTestCase, forum, thread, post as forum_post)
from kitsune.sumo.tests import get, post
from kitsune.sumo.urlresolvers import reverse
from kitsune.users.tests import user, group


class PostPermissionsTests(ForumTestCase):
    """Test post views permissions."""

    def test_read_without_permission(self):
        """Listing posts without the view_in_forum permission should 404."""
        restricted_forum = _restricted_forum()
        t = thread(forum=restricted_forum, save=True)

        response = get(self.client, 'forums.posts', args=[t.forum.slug, t.id])
        eq_(404, response.status_code)

    def test_reply_without_view_permission(self):
        """Posting without view_in_forum permission should 404."""
        restricted_forum = _restricted_forum()
        t = thread(forum=restricted_forum, save=True)
        u = user(save=True)

        self.client.login(username=u.username, password='testpass')
        response = post(self.client, 'forums.reply', {'content': 'Blahs'},
                        args=[t.forum.slug, t.id])
        eq_(404, response.status_code)

    def test_reply_without_post_permission(self):
        """Posting without post_in_forum permission should 403."""
        restricted_forum = _restricted_forum(
            permission_code='forums_forum.post_in_forum')
        t = thread(forum=restricted_forum, save=True)
        u = user(save=True)

        self.client.login(username=u.username, password='testpass')
        with patch.object(Forum, 'allows_viewing_by', Mock(return_value=True)):
            response = post(self.client, 'forums.reply', {'content': 'Blahs'},
                            args=[t.forum.slug, t.id])
        eq_(403, response.status_code)

    def test_reply_thread_405(self):
        """Replying to a thread via a GET instead of a POST request."""
        t = thread(save=True)
        u = user(save=True)

        self.client.login(username=u.username, password='testpass')
        response = get(self.client, 'forums.reply',
                       args=[t.forum.slug, t.id])
        eq_(405, response.status_code)


class ThreadAuthorityPermissionsTests(ForumTestCase):
    """Test thread views authority permissions."""

    def test_new_thread_without_view_permission(self):
        """Making a new thread without view permission should 404."""
        restricted_forum = _restricted_forum()
        thread(forum=restricted_forum, save=True)
        u = user(save=True)

        self.client.login(username=u.username, password='testpass')
        response = post(self.client, 'forums.new_thread',
                        {'title': 'Blahs', 'content': 'Blahs'},
                        args=[restricted_forum.slug])
        eq_(404, response.status_code)

    def test_new_thread_without_post_permission(self):
        """Making a new thread without post permission should 403."""
        restricted_forum = _restricted_forum(
            permission_code='forums_forum.post_in_forum')
        u = user(save=True)

        self.client.login(username=u.username, password='testpass')
        with patch.object(Forum, 'allows_viewing_by', Mock(return_value=True)):
            response = post(self.client, 'forums.new_thread',
                            {'title': 'Blahs', 'content': 'Blahs'},
                            args=[restricted_forum.slug])
        eq_(403, response.status_code)

    def test_watch_GET_405(self):
        """Watch forum with HTTP GET results in 405."""
        f = forum(save=True)
        u = user(save=True)

        self.client.login(username=u.username, password='testpass')
        response = get(self.client, 'forums.watch_forum', args=[f.id])
        eq_(405, response.status_code)

    def test_watch_forum_without_permission(self):
        """Watching forums without the view_in_forum permission should 404.
        """
        restricted_forum = _restricted_forum()
        u = user(save=True)

        self.client.login(username=u.username, password='testpass')
        response = self.client.post(reverse('forums.watch_forum',
                                            args=[restricted_forum.slug]),
                                    {'watch': 'yes'}, follow=False)
        eq_(404, response.status_code)

    def test_watch_thread_without_permission(self):
        """Watching threads without the view_in_forum permission should 404.
        """
        restricted_forum = _restricted_forum()
        t = thread(forum=restricted_forum, save=True)
        u = user(save=True)

        self.client.login(username=u.username, password='testpass')
        response = self.client.post(reverse('forums.watch_thread',
                                            args=[t.forum.slug, t.id]),
                                    {'watch': 'yes'}, follow=False)
        eq_(404, response.status_code)

    def test_read_without_permission(self):
        """Listing threads without the view_in_forum permission should 404.
        """
        restricted_forum = _restricted_forum()

        response = get(self.client, 'forums.threads',
                       args=[restricted_forum.slug])
        eq_(404, response.status_code)


class ThreadTests(ForumTestCase):
    """Test thread views."""

    def test_watch_forum(self):
        """Watch then unwatch a forum."""
        f = forum(save=True)
        forum_post(thread=thread(forum=f, save=True), save=True)
        u = user(save=True)

        self.client.login(username=u.username, password='testpass')

        post(self.client, 'forums.watch_forum', {'watch': 'yes'},
             args=[f.slug])
        assert NewThreadEvent.is_notifying(u, f)
        # NewPostEvent is not notifying.
        assert not NewPostEvent.is_notifying(u, f.last_post)

        post(self.client, 'forums.watch_forum', {'watch': 'no'},
             args=[f.slug])
        assert not NewThreadEvent.is_notifying(u, f)

    def test_watch_thread(self):
        """Watch then unwatch a thread."""
        t = thread(save=True)
        u = user(save=True)

        self.client.login(username=u.username, password='testpass')

        post(self.client, 'forums.watch_thread', {'watch': 'yes'},
             args=[t.forum.slug, t.id])
        assert NewPostEvent.is_notifying(u, t)
        # NewThreadEvent is not notifying.
        assert not NewThreadEvent.is_notifying(u, t.forum)

        post(self.client, 'forums.watch_thread', {'watch': 'no'},
             args=[t.forum.slug, t.id])
        assert not NewPostEvent.is_notifying(u, t)

    def test_edit_thread_creator(self):
        """Changing thread title as the thread creator works."""
        t = forum_post(save=True).thread
        u = t.creator

        self.client.login(username=u.username, password='testpass')
        post(self.client, 'forums.edit_thread', {'title': 'A new title'},
             args=[t.forum.slug, t.id])
        edited_t = Thread.uncached.get(id=t.id)
        eq_('A new title', edited_t.title)

    def test_edit_thread_moderator(self):
        """Editing post as a moderator works."""
        t = forum_post(save=True).thread
        f = t.forum
        u = user(save=True)
        g = group(save=True)
        ct = ContentType.objects.get_for_model(f)
        permission(codename='forums_forum.thread_edit_forum', content_type=ct,
                   object_id=f.id, group=g, save=True)
        g.user_set.add(u)

        self.client.login(username=u.username, password='testpass')
        r = post(self.client, 'forums.edit_thread',
                 {'title': 'new title'}, args=[f.slug, t.id])
        eq_(200, r.status_code)
        edited_t = Thread.uncached.get(id=t.id)
        eq_('new title', edited_t.title)

    def test_new_thread_redirect(self):
        """Posting a new thread should redirect."""
        f = forum(save=True)
        u = user(save=True)

        self.client.login(username=u.username, password='testpass')
        url = reverse('forums.new_thread', args=[f.slug])
        data = {'title': 'some title', 'content': 'some content'}
        r = self.client.post(url, data, follow=False)
        eq_(302, r.status_code)
        assert f.slug in r['location']
        assert 'last=' in r['location']

    def test_reply_redirect(self):
        """Posting a reply should redirect."""
        t = thread(save=True)
        u = user(save=True)

        self.client.login(username=u.username, password='testpass')
        url = reverse('forums.reply', args=[t.forum.slug, t.id])
        data = {'content': 'some content'}
        r = self.client.post(url, data, follow=False)
        eq_(302, r.status_code)
        assert t.forum.slug in r['location']
        assert str(t.id) in r['location']
        assert 'last=' in r['location']


class ThreadPermissionsTests(ForumTestCase):
    def test_edit_thread_403(self):
        """Editing a thread without permissions returns 403."""
        t = forum_post(save=True).thread
        u = user(save=True)

        self.client.login(username=u.username, password='testpass')
        response = get(self.client, 'forums.edit_thread',
                       args=[t.forum.slug, t.id])
        eq_(403, response.status_code)

    def test_edit_locked_thread_403(self):
        """Editing a locked thread returns 403."""
        locked = thread(is_locked=True, save=True)
        u = locked.creator
        forum_post(thread=locked, author=u, save=True)

        self.client.login(username=u.username, password='testpass')
        response = get(self.client, 'forums.edit_thread',
                       args=[locked.forum.slug, locked.id])
        eq_(403, response.status_code)

    def test_delete_thread_403(self):
        """Deleting a thread without permissions returns 403."""
        t = forum_post(save=True).thread
        u = user(save=True)

        self.client.login(username=u.username, password='testpass')
        response = get(self.client, 'forums.delete_thread',
                       args=[t.forum.slug, t.id])
        eq_(403, response.status_code)

    def test_sticky_thread_405(self):
        """Marking a thread sticky with a HTTP GET returns 405."""
        t = forum_post(save=True).thread
        u = user(save=True)

        self.client.login(username=u.username, password='testpass')
        response = get(self.client, 'forums.sticky_thread',
                       args=[t.forum.slug, t.id])
        eq_(405, response.status_code)

    def test_sticky_thread_403(self):
        """Marking a thread sticky without permissions returns 403."""
        t = forum_post(save=True).thread
        u = user(save=True)

        self.client.login(username=u.username, password='testpass')
        response = post(self.client, 'forums.sticky_thread',
                        args=[t.forum.slug, t.id])
        eq_(403, response.status_code)

    def test_locked_thread_403(self):
        """Marking a thread locked without permissions returns 403."""
        t = forum_post(save=True).thread
        u = user(save=True)

        self.client.login(username=u.username, password='testpass')
        response = post(self.client, 'forums.lock_thread',
                        args=[t.forum.slug, t.id])
        eq_(403, response.status_code)

    def test_locked_thread_405(self):
        """Marking a thread locked via a GET instead of a POST request."""
        t = forum_post(save=True).thread
        u = user(save=True)

        self.client.login(username=u.username, password='testpass')
        response = get(self.client, 'forums.lock_thread',
                       args=[t.forum.slug, t.id])
        eq_(405, response.status_code)

    def test_move_thread_403(self):
        """Moving a thread without permissions returns 403."""
        t = forum_post(save=True).thread
        f = forum(save=True)
        u = user(save=True)

        self.client.login(username=u.username, password='testpass')
        response = post(self.client, 'forums.move_thread', {'forum': f.id},
                        args=[t.forum.slug, t.id])
        eq_(403, response.status_code)

    def test_move_thread_405(self):
        """Moving a thread via a GET instead of a POST request."""
        t = forum_post(save=True).thread
        u = user(save=True)

        self.client.login(username=u.username, password='testpass')
        response = get(self.client, 'forums.move_thread',
                       args=[t.forum.slug, t.id])
        eq_(405, response.status_code)

    def test_move_thread(self):
        """Move a thread."""
        t = forum_post(save=True).thread
        f = forum(save=True)
        u = user(save=True)
        g = group(save=True)

        # Give the user permission to move threads between the two forums.
        ct = ContentType.objects.get_for_model(f)
        permission(codename='forums_forum.thread_move_forum', content_type=ct,
                   object_id=f.id, group=g, save=True)
        permission(codename='forums_forum.thread_move_forum', content_type=ct,
                   object_id=t.forum.id, group=g, save=True)
        g.user_set.add(u)

        self.client.login(username=u.username, password='testpass')
        response = post(self.client, 'forums.move_thread',
                        {'forum': f.id},
                        args=[t.forum.slug, t.id])
        eq_(200, response.status_code)
        t = Thread.uncached.get(pk=t.pk)
        eq_(f.id, t.forum.id)

    def test_post_edit_403(self):
        """Editing a post without permissions returns 403."""
        p = forum_post(save=True)
        t = p.thread
        u = user(save=True)

        self.client.login(username=u.username, password='testpass')
        response = get(self.client, 'forums.edit_post',
                       args=[t.forum.slug, t.id, p.id])
        eq_(403, response.status_code)

    def test_post_delete_403(self):
        """Deleting a post without permissions returns 403."""
        p = forum_post(save=True)
        t = p.thread
        u = user(save=True)

        self.client.login(username=u.username, password='testpass')
        response = get(self.client, 'forums.delete_post',
                       args=[t.forum.slug, t.id, p.id])
        eq_(403, response.status_code)


def _restricted_forum(permission_code='forums_forum.view_in_forum'):
    """Return a forum with specified restriction."""
    restricted_forum = forum(save=True)

    # Make it restricted.
    ct = ContentType.objects.get_for_model(restricted_forum)
    permission(codename=permission_code, content_type=ct,
               object_id=restricted_forum.id, save=True)

    return restricted_forum
