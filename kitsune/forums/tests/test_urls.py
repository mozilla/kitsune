from django.contrib.contenttypes.models import ContentType

from nose.tools import eq_

from kitsune.access.tests import permission
from kitsune.forums.tests import (
    ForumTestCase, forum, thread, post as forum_post)
from kitsune.sumo.tests import get, post
from kitsune.users.tests import user, group


class BelongsTestCase(ForumTestCase):
    """
    Mixing and matching thread, forum, and post data in URLs should fail.
    """

    def test_posts_thread_belongs_to_forum(self):
        """Posts view - redirect if thread does not belong to forum."""
        f = forum(save=True)
        t = thread(save=True)  # Thread belongs to a different forum

        r = get(self.client, 'forums.posts', args=[f.slug, t.id])
        eq_(200, r.status_code)
        u = r.redirect_chain[0][0]
        assert u.endswith(t.get_absolute_url())

    def test_reply_thread_belongs_to_forum(self):
        """Reply action - thread belongs to forum."""
        f = forum(save=True)
        t = thread(save=True)  # Thread belongs to a different forum
        u = user(save=True)

        self.client.login(username=u.username, password='testpass')
        r = post(self.client, 'forums.reply', {}, args=[f.slug, t.id])
        eq_(404, r.status_code)

    def test_locked_thread_belongs_to_forum(self):
        """Lock action - thread belongs to forum."""
        f = forum(save=True)
        t = thread(save=True)  # Thread belongs to a different forum
        u = user(save=True)

        # Give the user the permission to lock threads.
        g = group(save=True)
        ct = ContentType.objects.get_for_model(f)
        permission(codename='forums_forum.thread_locked_forum',
                   content_type=ct, object_id=f.id, group=g, save=True)
        permission(codename='forums_forum.thread_locked_forum',
                   content_type=ct, object_id=t.forum.id, group=g, save=True)
        g.user_set.add(u)

        self.client.login(username=u.username, password='testpass')
        r = post(self.client, 'forums.lock_thread', {}, args=[f.slug, t.id])
        eq_(404, r.status_code)

    def test_sticky_thread_belongs_to_forum(self):
        """Sticky action - thread belongs to forum."""
        f = forum(save=True)
        t = thread(save=True)  # Thread belongs to a different forum
        u = user(save=True)

        # Give the user the permission to sticky threads.
        g = group(save=True)
        ct = ContentType.objects.get_for_model(f)
        permission(codename='forums_forum.thread_sticky_forum',
                   content_type=ct, object_id=f.id, group=g, save=True)
        permission(codename='forums_forum.thread_sticky_forum',
                   content_type=ct, object_id=t.forum.id, group=g, save=True)
        g.user_set.add(u)

        self.client.login(username=u.username, password='testpass')
        r = post(self.client, 'forums.sticky_thread', {}, args=[f.slug, t.id])
        eq_(404, r.status_code)

    def test_edit_thread_belongs_to_forum(self):
        """Edit thread action - thread belongs to forum."""
        f = forum(save=True)
        t = forum_post(save=True).thread  # Thread belongs to a different forum
        u = t.creator

        self.client.login(username=u.username, password='testpass')
        r = get(self.client, 'forums.edit_thread', args=[f.slug, t.id])
        eq_(404, r.status_code)

    def test_delete_thread_belongs_to_forum(self):
        """Delete thread action - thread belongs to forum."""
        f = forum(save=True)
        t = thread(save=True)  # Thread belongs to a different forum
        u = user(save=True)

        # Give the user the permission to delete threads.
        g = group(save=True)
        ct = ContentType.objects.get_for_model(f)
        permission(codename='forums_forum.thread_delete_forum',
                   content_type=ct, object_id=f.id, group=g, save=True)
        permission(codename='forums_forum.thread_delete_forum',
                   content_type=ct, object_id=t.forum.id, group=g, save=True)
        g.user_set.add(u)

        self.client.login(username=u.username, password='testpass')
        r = get(self.client, 'forums.delete_thread', args=[f.slug, t.id])
        eq_(404, r.status_code)

    def test_edit_post_belongs_to_thread_and_forum(self):
        # Edit post action - post belongs to thread and thread belongs
        # to forum.
        f = forum(save=True)
        t = thread(forum=f, save=True)
        # Post belongs to a different forum and thread.
        p = forum_post(save=True)
        u = p.author

        self.client.login(username=u.username, password='testpass')

        # Post isn't in the passed forum:
        r = get(self.client, 'forums.edit_post',
                args=[f.slug, p.thread.id, p.id])
        eq_(404, r.status_code)

        # Post isn't in the passed thread:
        r = get(self.client, 'forums.edit_post',
                args=[p.thread.forum.slug, t.id, p.id])
        eq_(404, r.status_code)

    def test_delete_post_belongs_to_thread_and_forum(self):
        # Delete post action - post belongs to thread and thread
        # belongs to forum.
        f = forum(save=True)
        t = thread(forum=f, save=True)
        # Post belongs to a different forum and thread.
        p = forum_post(save=True)
        u = p.author

        # Give the user the permission to delete posts.
        g = group(save=True)
        ct = ContentType.objects.get_for_model(f)
        permission(codename='forums_forum.post_delete_forum',
                   content_type=ct, object_id=p.thread.forum_id, group=g,
                   save=True)
        permission(codename='forums_forum.post_delete_forum',
                   content_type=ct, object_id=f.id, group=g, save=True)
        g.user_set.add(u)

        self.client.login(username=u.username, password='testpass')

        # Post isn't in the passed forum:
        r = get(self.client, 'forums.delete_post',
                args=[f.slug, p.thread.id, p.id])
        eq_(404, r.status_code)

        # Post isn't in the passed thread:
        r = get(self.client, 'forums.delete_post',
                args=[p.thread.forum.slug, t.id, p.id])
        eq_(404, r.status_code)
