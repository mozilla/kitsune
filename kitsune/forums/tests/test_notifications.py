from django.contrib import admin
from django.contrib.admin.options import ModelAdmin
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.sites.models import Site
from django.core import mail
from django.test.client import RequestFactory
from tidings.models import Watch

import mock
from nose.tools import eq_

from kitsune.forums.events import NewPostEvent, NewThreadEvent
from kitsune.forums.models import Thread, Post
from kitsune.forums.tests import (
    ForumTestCase, ThreadFactory, ForumFactory, PostFactory)
from kitsune.sumo.urlresolvers import reverse
from kitsune.sumo.tests import post, attrs_eq, starts_with
from kitsune.users.models import Setting
from kitsune.users.tests import UserFactory


# Some of these contain a locale prefix on included links, while
# others don't.  This depends on whether the tests use them inside or
# outside the scope of a request. See the long explanation in
# questions.tests.test_notifications.
REPLY_EMAIL = """Reply to thread: {thread}

{username} has replied to a thread you're watching. Here is their reply:

========

a post

========

To view this post on the site, click the following link, or paste it into \
your browser's location bar:

https://testserver/en-US/forums/{forum_slug}/{thread_id}?utm_campaign=\
forums-post&utm_source=notification&utm_medium=email#post-{post_id}

--
Unsubscribe from these emails:
https://testserver/en-US/unsubscribe/{watch_id}?s={watch_secret}"""

NEW_THREAD_EMAIL = """New thread: {thread}

{username} has posted a new thread in a forum you're watching. Here is \
the thread:

========

a post

========

To view this post on the site, click the following link, or paste it into \
your browser's location bar:

https://testserver/en-US/forums/{forum_slug}/{thread_id}?utm_campaign=\
forums-thread&utm_source=notification&utm_medium=email

--
Unsubscribe from these emails:
https://testserver/en-US/unsubscribe/{watch_id}?s={watch_secret}"""


def get_watch_for(obj):
    """"""
    ct = ContentType.objects.get_for_model(obj)
    return Watch.objects.filter(content_type=ct, object_id=obj.id)


class NotificationsTests(ForumTestCase):
    """Test that notifications get sent."""

    @mock.patch.object(NewPostEvent, 'fire')
    def test_fire_on_reply(self, fire):
        """The event fires when there is a reply."""
        u = UserFactory()
        t = ThreadFactory()
        self.client.login(username=u.username, password='testpass')
        post(self.client, 'forums.reply', {'content': 'a post'},
             args=[t.forum.slug, t.id])
        # NewPostEvent.fire() is called.
        assert fire.called

    @mock.patch.object(NewThreadEvent, 'fire')
    def test_fire_on_new_thread(self, fire):
        """The event fires when there is a new thread."""
        u = UserFactory()
        f = ForumFactory()
        self.client.login(username=u.username, password='testpass')
        post(self.client, 'forums.new_thread',
             {'title': 'a title', 'content': 'a post'},
             args=[f.slug])
        # NewThreadEvent.fire() is called.
        assert fire.called

    def _toggle_watch_thread_as(self, thread, user, turn_on=True):
        """Watch a thread and return it."""
        self.client.login(username=user.username, password='testpass')
        watch = 'yes' if turn_on else 'no'
        post(self.client, 'forums.watch_thread', {'watch': watch},
             args=[thread.forum.slug, thread.id])
        # Watch exists or not, depending on watch.
        if turn_on:
            assert NewPostEvent.is_notifying(user, thread), (
                'NewPostEvent should be notifying.')
        else:
            assert not NewPostEvent.is_notifying(user, thread), (
                'NewPostEvent should not be notifying.')

    def _toggle_watch_forum_as(self, forum, user, turn_on=True):
        """Watch a forum and return it."""
        self.client.login(username=user.username, password='testpass')
        watch = 'yes' if turn_on else 'no'
        post(self.client, 'forums.watch_forum', {'watch': watch},
             args=[forum.slug])
        # Watch exists or not, depending on watch.
        if turn_on:
            assert NewThreadEvent.is_notifying(user, forum), (
                'NewThreadEvent should be notifying.')
        else:
            assert not NewPostEvent.is_notifying(user, forum), (
                'NewThreadEvent should not be notifying.')

    @mock.patch.object(Site.objects, 'get_current')
    def test_watch_thread_then_reply(self, get_current):
        """The event fires and sends emails when watching a thread."""
        get_current.return_value.domain = 'testserver'

        t = ThreadFactory()
        f = t.forum
        poster = UserFactory()
        watcher = UserFactory()

        self._toggle_watch_thread_as(t, watcher, turn_on=True)
        self.client.login(username=poster.username, password='testpass')
        post(self.client, 'forums.reply', {'content': 'a post'},
             args=[t.forum.slug, t.id])

        p = Post.objects.all().order_by('-id')[0]
        w = get_watch_for(f).order_by('-id')[0]
        attrs_eq(mail.outbox[0], to=[watcher.email],
                 subject='Re: {f} - {t}'.format(f=f, t=t))
        body = REPLY_EMAIL.format(
            username=poster.profile.name,
            forum_slug=f.slug,
            thread=t.title,
            thread_id=t.id,
            post_id=p.id,
            watch_id=w.id,
            watch_secret=w.secret)
        starts_with(mail.outbox[0].body, body)

    def test_watch_other_thread_then_reply(self):
        # Watching a different thread than the one we're replying to
        # shouldn't notify.
        t1 = ThreadFactory()
        t2 = ThreadFactory()
        poster = UserFactory()
        watcher = UserFactory()

        self._toggle_watch_thread_as(t1, watcher, turn_on=True)
        self.client.login(username=poster.username, password='testpass')
        post(self.client, 'forums.reply', {'content': 'a post'},
             args=[t2.forum.slug, t2.id])

        assert not mail.outbox

    @mock.patch.object(Site.objects, 'get_current')
    def test_watch_forum_then_new_thread(self, get_current):
        """Watching a forum and creating a new thread should send email."""
        get_current.return_value.domain = 'testserver'

        f = ForumFactory()
        poster = UserFactory(username='POSTER', profile__name='Poster')
        watcher = UserFactory(username='WATCHER', profile__name='Watcher')

        self._toggle_watch_forum_as(f, watcher, turn_on=True)
        self.client.login(username=poster.username, password='testpass')
        post(self.client, 'forums.new_thread',
             {'title': 'a title', 'content': 'a post'}, args=[f.slug])

        t = Thread.objects.all().order_by('-id')[0]
        w = get_watch_for(f).order_by('-id')[0]
        attrs_eq(mail.outbox[0], to=[watcher.email], subject='{f} - {t}'.format(f=f, t=t))
        body = NEW_THREAD_EMAIL.format(
            username=poster.profile.name,
            forum_slug=f.slug,
            thread=t.title,
            thread_id=t.id,
            watch_id=w.id,
            watch_secret=w.secret)
        starts_with(mail.outbox[0].body, body)

    @mock.patch.object(Site.objects, 'get_current')
    def test_watch_forum_then_new_thread_as_self(self, get_current):
        # Watching a forum and creating a new thread as myself should
        # not send email.
        get_current.return_value.domain = 'testserver'

        f = ForumFactory()
        watcher = UserFactory()

        self._toggle_watch_forum_as(f, watcher, turn_on=True)
        self.client.login(username=watcher.username, password='testpass')
        post(self.client, 'forums.new_thread',
             {'title': 'a title', 'content': 'a post'}, args=[f.slug])
        # Assert no email is sent.
        assert not mail.outbox

    @mock.patch.object(Site.objects, 'get_current')
    def test_watch_forum_then_new_post(self, get_current):
        """Watching a forum and replying to a thread should send email."""
        get_current.return_value.domain = 'testserver'

        t = ThreadFactory()
        f = t.forum
        PostFactory(thread=t)
        poster = UserFactory()
        watcher = UserFactory()

        self._toggle_watch_forum_as(f, watcher, turn_on=True)
        self.client.login(username=poster.username, password='testpass')
        post(self.client, 'forums.reply', {'content': 'a post'},
             args=[f.slug, t.id])

        p = Post.objects.all().order_by('-id')[0]
        w = get_watch_for(f).order_by('-id')[0]
        attrs_eq(mail.outbox[0], to=[watcher.email],
                 subject='Re: {f} - {t}'.format(f=f, t=t))
        body = REPLY_EMAIL.format(
            username=poster.profile.name,
            forum_slug=f.slug,
            thread=t.title,
            thread_id=t.id,
            post_id=p.id,
            watch_id=w.id,
            watch_secret=w.secret)
        starts_with(mail.outbox[0].body, body)

    @mock.patch.object(Site.objects, 'get_current')
    def test_watch_forum_then_new_post_as_self(self, get_current):
        """Watching a forum and replying as myself should not send email."""
        get_current.return_value.domain = 'testserver'

        t = ThreadFactory()
        f = t.forum
        PostFactory(thread=t)
        watcher = UserFactory()

        self._toggle_watch_forum_as(f, watcher, turn_on=True)
        self.client.login(username=watcher.username, password='testpass')
        post(self.client, 'forums.reply', {'content': 'a post'},
             args=[f.slug, t.id])
        # Assert no email is sent.
        assert not mail.outbox

    @mock.patch.object(Site.objects, 'get_current')
    def test_watch_both_then_new_post(self, get_current):
        """Watching both forum and thread.

        Replying to a thread should send ONE email."""
        get_current.return_value.domain = 'testserver'

        t = ThreadFactory()
        f = t.forum
        PostFactory(thread=t)
        poster = UserFactory()
        watcher = UserFactory()

        self._toggle_watch_forum_as(f, watcher, turn_on=True)
        self._toggle_watch_thread_as(t, watcher, turn_on=True)
        self.client.login(username=poster.username, password='testpass')
        post(self.client, 'forums.reply', {'content': 'a post'},
             args=[f.slug, t.id])

        eq_(1, len(mail.outbox))
        p = Post.objects.all().order_by('-id')[0]
        w = get_watch_for(f).order_by('-id')[0]
        attrs_eq(mail.outbox[0], to=[watcher.email],
                 subject='Re: {f} - {t}'.format(f=f, t=t))
        body = REPLY_EMAIL.format(
            username=poster.profile.name,
            forum_slug=f.slug,
            thread=t.title,
            thread_id=t.id,
            post_id=p.id,
            watch_id=w.id,
            watch_secret=w.secret)
        starts_with(mail.outbox[0].body, body)

    @mock.patch.object(Site.objects, 'get_current')
    def test_autowatch_new_thread(self, get_current):
        """Creating a new thread should email responses"""
        get_current.return_value.domain = 'testserver'

        f = ForumFactory()
        u = UserFactory()

        self.client.login(username=u.username, password='testpass')
        s = Setting.objects.create(user=u, name='forums_watch_new_thread',
                                   value='False')
        data = {'title': 'a title', 'content': 'a post'}
        post(self.client, 'forums.new_thread', data, args=[f.slug])
        t1 = Thread.objects.all().order_by('-id')[0]
        assert not NewPostEvent.is_notifying(u, t1), (
            'NewPostEvent should not be notifying.')

        s.value = 'True'
        s.save()
        post(self.client, 'forums.new_thread', data, args=[f.slug])
        t2 = Thread.objects.all().order_by('-id')[0]
        assert NewPostEvent.is_notifying(u, t2), (
            'NewPostEvent should be notifying.')

    @mock.patch.object(Site.objects, 'get_current')
    def test_autowatch_reply(self, get_current):
        """Replying to a thread creates a watch."""
        get_current.return_value.domain = 'testserver'

        u = UserFactory()
        t1 = ThreadFactory()
        t2 = ThreadFactory()

        assert not NewPostEvent.is_notifying(u, t1)
        assert not NewPostEvent.is_notifying(u, t2)

        self.client.login(username=u.username, password='testpass')

        # If the poster has the forums_watch_after_reply setting set to True,
        # they will start watching threads they reply to.
        s = Setting.objects.create(user=u, name='forums_watch_after_reply',
                                   value='True')
        data = {'content': 'some content'}
        post(self.client, 'forums.reply', data, args=[t1.forum.slug, t1.pk])
        assert NewPostEvent.is_notifying(u, t1)

        # Setting forums_watch_after_reply back to False, now they shouldn't
        # start watching threads they reply to.
        s.value = 'False'
        s.save()
        post(self.client, 'forums.reply', data, args=[t2.forum.slug, t2.pk])
        assert not NewPostEvent.is_notifying(u, t2)

    @mock.patch.object(Site.objects, 'get_current')
    def test_admin_delete_user_with_watched_thread(self, get_current):
        """Test the admin delete view for a user with a watched thread."""
        get_current.return_value.domain = 'testserver'

        t = ThreadFactory()
        u = t.creator
        watcher = UserFactory()
        admin_user = UserFactory(is_staff=True, is_superuser=True)

        self.client.login(username=admin_user.username, password='testpass')
        self._toggle_watch_thread_as(t, watcher, turn_on=True)
        url = reverse('admin:auth_user_delete', args=[u.id])
        # url = reverse('admin:users_profile_delete', args=[u.id])
        request = RequestFactory().get(url)
        request.user = admin_user
        request.session = self.client.session
        # The following blows up without our monkeypatch.
        ModelAdmin(User, admin.site).delete_view(request, str(u.id))
