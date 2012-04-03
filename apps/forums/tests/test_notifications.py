from django.contrib import admin
from django.contrib.admin.options import ModelAdmin
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.core import mail

import mock
from nose.tools import eq_
import test_utils

from forums.events import NewPostEvent, NewThreadEvent
from forums.models import Thread, Forum, Post
from forums.tests import OldForumTestCase
from sumo.urlresolvers import reverse
from sumo.tests import post, attrs_eq, starts_with
from users.models import Setting
from users.tests import user


# Some of these contain a locale prefix on included links, while others don't.
# This depends on whether the tests use them inside or outside the scope of a
# request. See the long explanation in questions.tests.test_notifications.
REPLY_EMAIL = u"""Reply to thread: Sticky Thread

User jsocol has replied to a thread you're watching. Here
is their reply:

========

a post

========

To view this post on the site, click the following link, or
paste it into your browser's location bar:

https://testserver/en-US/forums/test-forum/2#post-%s

--
Unsubscribe from these emails:
https://testserver/en-US/unsubscribe/"""

NEW_THREAD_EMAIL = u"""New thread: a title

User jsocol has posted a new thread in a forum you're watching.
Here is the thread:

========

a post

========

To view this post on the site, click the following link, or
paste it into your browser's location bar:

https://testserver/en-US/forums/test-forum/%s

--
Unsubscribe from these emails:
https://testserver/en-US/unsubscribe/"""


class NotificationsTests(OldForumTestCase):
    """Test that notifications get sent."""

    @mock.patch.object(NewPostEvent, 'fire')
    def test_fire_on_reply(self, fire):
        """The event fires when there is a reply."""
        t = Thread.objects.get(pk=2)
        self.client.login(username='jsocol', password='testpass')
        post(self.client, 'forums.reply', {'content': 'a post'},
             args=[t.forum.slug, t.id])
        # NewPostEvent.fire() is called.
        assert fire.called

    @mock.patch.object(NewThreadEvent, 'fire')
    def test_fire_on_new_thread(self, fire):
        """The event fires when there is a new thread."""
        f = Forum.objects.get(pk=1)
        self.client.login(username='jsocol', password='testpass')
        post(self.client, 'forums.new_thread',
             {'title': 'a title', 'content': 'a post'},
             args=[f.slug])
        # NewThreadEvent.fire() is called.
        assert fire.called

    def _toggle_watch_thread_as(self, username, turn_on=True, thread_id=2):
        """Watch a thread and return it."""
        thread = Thread.objects.get(pk=thread_id)
        self.client.login(username=username, password='testpass')
        user = User.objects.get(username=username)
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
        return thread

    def _toggle_watch_forum_as(self, username, turn_on=True, forum_id=1):
        """Watch a forum and return it."""
        forum = Forum.objects.get(pk=forum_id)
        self.client.login(username=username, password='testpass')
        user = User.objects.get(username=username)
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
        return forum

    @mock.patch.object(Site.objects, 'get_current')
    def test_watch_thread_then_reply(self, get_current):
        """The event fires and sends emails when watching a thread."""
        get_current.return_value.domain = 'testserver'

        t = self._toggle_watch_thread_as('pcraciunoiu', turn_on=True)
        self.client.login(username='jsocol', password='testpass')
        post(self.client, 'forums.reply', {'content': 'a post'},
             args=[t.forum.slug, t.id])

        p = Post.objects.all().order_by('-id')[0]
        attrs_eq(mail.outbox[0], to=['user47963@nowhere'],
                 subject='Re: Test forum - Sticky Thread')
        starts_with(mail.outbox[0].body, REPLY_EMAIL % p.id)

        self._toggle_watch_thread_as('pcraciunoiu', turn_on=False)

    def test_watch_other_thread_then_reply(self):
        """Watching a different thread than the one we're replying to shouldn't
        notify."""
        t = self._toggle_watch_thread_as('pcraciunoiu', turn_on=True)
        t2 = Thread.objects.exclude(pk=t.pk)[0]
        self.client.login(username='jsocol', password='testpass')
        post(self.client, 'forums.reply', {'content': 'a post'},
             args=[t2.forum.slug, t2.id])

        assert not mail.outbox

    @mock.patch.object(Site.objects, 'get_current')
    def test_watch_forum_then_new_thread(self, get_current):
        """Watching a forum and creating a new thread should send email."""
        get_current.return_value.domain = 'testserver'

        f = self._toggle_watch_forum_as('pcraciunoiu', turn_on=True)
        self.client.login(username='jsocol', password='testpass')
        post(self.client, 'forums.new_thread',
             {'title': 'a title', 'content': 'a post'}, args=[f.slug])

        t = Thread.objects.all().order_by('-id')[0]
        attrs_eq(mail.outbox[0], to=['user47963@nowhere'],
                 subject='Test forum - a title')
        starts_with(mail.outbox[0].body, NEW_THREAD_EMAIL % t.id)

        self._toggle_watch_forum_as('pcraciunoiu', turn_on=False)

    @mock.patch.object(Site.objects, 'get_current')
    def test_watch_forum_then_new_thread_as_self(self, get_current):
        """Watching a forum and creating a new thread as myself should not
        send email."""
        get_current.return_value.domain = 'testserver'

        f = self._toggle_watch_forum_as('pcraciunoiu', turn_on=True)
        self.client.login(username='pcraciunoiu', password='testpass')
        post(self.client, 'forums.new_thread',
             {'title': 'a title', 'content': 'a post'}, args=[f.slug])
        # Assert no email is sent.
        assert not mail.outbox

    @mock.patch.object(Site.objects, 'get_current')
    def test_watch_forum_then_new_post(self, get_current):
        """Watching a forum and replying to a thread should send email."""
        get_current.return_value.domain = 'testserver'

        f = self._toggle_watch_forum_as('pcraciunoiu', turn_on=True)
        t = f.thread_set.all()[0]
        self.client.login(username='jsocol', password='testpass')
        post(self.client, 'forums.reply', {'content': 'a post'},
             args=[f.slug, t.id])

        p = Post.objects.all().order_by('-id')[0]
        attrs_eq(mail.outbox[0], to=['user47963@nowhere'],
                 subject='Re: Test forum - Sticky Thread')
        starts_with(mail.outbox[0].body, REPLY_EMAIL % p.id)

    @mock.patch.object(Site.objects, 'get_current')
    def test_watch_forum_then_new_post_as_self(self, get_current):
        """Watching a forum and replying as myself should not send email."""
        get_current.return_value.domain = 'testserver'

        f = self._toggle_watch_forum_as('pcraciunoiu', turn_on=True)
        t = f.thread_set.all()[0]
        self.client.login(username='pcraciunoiu', password='testpass')
        post(self.client, 'forums.reply', {'content': 'a post'},
             args=[f.slug, t.id])
        # Assert no email is sent.
        assert not mail.outbox

    @mock.patch.object(Site.objects, 'get_current')
    def test_watch_both_then_new_post(self, get_current):
        """Watching both and replying to a thread should send ONE email."""
        get_current.return_value.domain = 'testserver'

        f = self._toggle_watch_forum_as('pcraciunoiu', turn_on=True)
        t = f.thread_set.all()[0]
        self._toggle_watch_thread_as('pcraciunoiu', turn_on=True,
                                     thread_id=t.id)
        self.client.login(username='jsocol', password='testpass')
        post(self.client, 'forums.reply', {'content': 'a post'},
             args=[f.slug, t.id])

        eq_(1, len(mail.outbox))
        p = Post.objects.all().order_by('-id')[0]
        attrs_eq(mail.outbox[0], to=['user47963@nowhere'],
                 subject='Re: Test forum - Sticky Thread')
        starts_with(mail.outbox[0].body, REPLY_EMAIL % p.id)

        self._toggle_watch_forum_as('pcraciunoiu', turn_on=False)
        self._toggle_watch_thread_as('pcraciunoiu', turn_on=False)

    @mock.patch.object(Site.objects, 'get_current')
    def test_autowatch_new_thread(self, get_current):
        """Creating a new thread should email responses"""
        get_current.return_value.domain = 'testserver'

        eq_(0, len(mail.outbox))
        f = Forum.objects.get(pk=1)
        self.client.login(username='jsocol', password='testpass')
        user = User.objects.get(username='jsocol')
        s = Setting.objects.create(user=user, name='forums_watch_new_thread',
                                   value='False')
        data = {'title': 'a title', 'content': 'a post'}
        post(self.client, 'forums.new_thread', data, args=[f.slug])
        t1 = Thread.objects.all().order_by('-id')[0]
        assert not NewPostEvent.is_notifying(user, t1), (
            'NewPostEvent should not be notifying.')

        s.value = 'True'
        s.save()
        post(self.client, 'forums.new_thread', data, args=[f.slug])
        t2 = Thread.uncached.all().order_by('-id')[0]
        assert NewPostEvent.is_notifying(user, t2), (
            'NewPostEvent should be notifying.')

    @mock.patch.object(Site.objects, 'get_current')
    def test_autowatch_reply(self, get_current):
        get_current.return_value.domain = 'testserver'

        user = User.objects.get(username='timw')
        t1, t2 = Thread.objects.filter(is_locked=False)[0:2]
        assert not NewPostEvent.is_notifying(user, t1)
        assert not NewPostEvent.is_notifying(user, t2)

        self.client.login(username='timw', password='testpass')
        s = Setting.objects.create(user=user, name='forums_watch_after_reply',
                                   value='True')
        data = {'content': 'some content'}
        post(self.client, 'forums.reply', data, args=[t1.forum.slug, t1.pk])
        assert NewPostEvent.is_notifying(user, t1)

        s.value = 'False'
        s.save()
        post(self.client, 'forums.reply', data, args=[t2.forum.slug, t2.pk])
        assert not NewPostEvent.is_notifying(user, t2)

    @mock.patch.object(Site.objects, 'get_current')
    def test_admin_delete_user_with_watched_thread(self, get_current):
        """Test the admin delete view for a user with a watched thread."""
        get_current.return_value.domain = 'testserver'
        self.client.login(username='admin', password='testpass')

        u = user(save=True)
        f = Forum.objects.all()[0]
        t = Thread(creator=u, forum=f, title='title')
        t.save()
        self._toggle_watch_thread_as('pcraciunoiu', thread_id=t.id, turn_on=True)
        url = reverse('admin:auth_user_delete', args=[u.id])
        request = test_utils.RequestFactory().get(url)
        request.user = User.objects.get(username='admin')
        request.session = self.client.session
        # The following blows up without our monkeypatch.
        ModelAdmin(User, admin.site).delete_view(request, str(u.id))
