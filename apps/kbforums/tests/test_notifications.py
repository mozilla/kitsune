from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.core import mail

import mock
from nose.tools import eq_

from kbforums.events import NewPostEvent, NewThreadEvent
from kbforums.models import Thread, Post
from kbforums.tests import KBForumTestCase, thread
from sumo.tests import post, attrs_eq, starts_with
from users.models import Setting
from users.tests import user
from wiki.tests import document


# Some of these contain a locale prefix on included links, while others don't.
# This depends on whether the tests use them inside or outside the scope of a
# request. See the long explanation in questions.tests.test_notifications.
REPLY_EMAIL = u"""Reply to thread: Sticky Thread

User jsocol has replied to a thread you're watching. Here is their reply:

========

a post

========

To view this post on the site, click the following link, or paste it into your browser's location bar:

https://testserver/en-US/kb/%s/discuss/%s#post-%s

--
Unsubscribe from these emails:
https://testserver/en-US/unsubscribe/"""
NEW_THREAD_EMAIL = u"""New thread: a title

User jsocol has posted a new thread in a forum you're watching. Here is the thread:

========

a post

========

To view this post on the site, click the following link, or paste it into your browser's location bar:

https://testserver/en-US/kb/%s/discuss/%s

--
Unsubscribe from these emails:
https://testserver/en-US/unsubscribe/"""


class NotificationsTests(KBForumTestCase):
    """Test that notifications get sent."""

    @mock.patch.object(NewPostEvent, 'fire')
    def test_fire_on_reply(self, fire):
        """The event fires when there is a reply."""
        t = thread(save=True)
        u = user(save=True)
        self.client.login(username=u.username, password='testpass')
        post(self.client, 'wiki.discuss.reply', {'content': 'a post'},
             args=[t.document.slug, t.id])
        # NewPostEvent.fire() is called.
        assert fire.called

    @mock.patch.object(NewThreadEvent, 'fire')
    def test_fire_on_new_thread(self, fire):
        """The event fires when there is a new thread."""
        d = document(save=True)
        u = user(save=True)
        self.client.login(username=u.username, password='testpass')
        post(self.client, 'wiki.discuss.new_thread',
             {'title': 'a title', 'content': 'a post'},
             args=[d.slug])
        # NewThreadEvent.fire() is called.
        assert fire.called

    def _toggle_watch_thread_as(self, username, thread, turn_on=True):
        """Watch a thread and return it."""
        self.client.login(username=username, password='testpass')
        user = User.objects.get(username=username)
        watch = 'yes' if turn_on else 'no'
        post(self.client, 'wiki.discuss.watch_thread', {'watch': watch},
             args=[thread.document.slug, thread.id])
        # Watch exists or not, depending on watch.
        if turn_on:
            assert NewPostEvent.is_notifying(user, thread), (
                'NewPostEvent should be notifying.')
        else:
            assert not NewPostEvent.is_notifying(user, thread), (
                'NewPostEvent should not be notifying.')
        return thread

    def _toggle_watch_kbforum_as(self, username, document, turn_on=True):
        """Watch a discussion forum and return it."""
        self.client.login(username=username, password='testpass')
        user = User.objects.get(username=username)
        watch = 'yes' if turn_on else 'no'
        post(self.client, 'wiki.discuss.watch_forum', {'watch': watch},
             args=[document.slug])
        # Watch exists or not, depending on watch.
        if turn_on:
            assert NewThreadEvent.is_notifying(user, document), (
                'NewThreadEvent should be notifying.')
        else:
            assert not NewThreadEvent.is_notifying(user, document), (
                'NewThreadEvent should not be notifying.')
        return document

    @mock.patch.object(Site.objects, 'get_current')
    def test_watch_thread_then_reply(self, get_current):
        """The event fires and sends emails when watching a thread."""
        get_current.return_value.domain = 'testserver'
        u = user(username='jsocol', save=True)
        u_b = user(username='berkerpeksag', save=True)
        d = document(title='an article title', save=True)
        _t = thread(title='Sticky Thread', document=d, is_sticky=True,
                    save=True)
        t = self._toggle_watch_thread_as(u_b.username, _t, turn_on=True)
        self.client.login(username=u.username, password='testpass')
        post(self.client, 'wiki.discuss.reply', {'content': 'a post'},
             args=[t.document.slug, t.id])

        p = Post.objects.all().order_by('-id')[0]
        attrs_eq(mail.outbox[0], to=[u_b.email],
                 subject='Re: an article title - Sticky Thread')
        starts_with(mail.outbox[0].body, REPLY_EMAIL % (d.slug, t.id, p.id))

        self._toggle_watch_thread_as(u_b.username, _t, turn_on=False)

    def test_watch_other_thread_then_reply(self):
        """Watching a different thread than the one we're replying to shouldn't
        notify."""
        u_b = user(username='berkerpeksag', save=True)
        _t = thread(save=True)
        self._toggle_watch_thread_as(u_b.username, _t, turn_on=True)
        u = user(save=True)
        t2 = thread(save=True)
        self.client.login(username=u.username, password='testpass')
        post(self.client, 'wiki.discuss.reply', {'content': 'a post'},
             args=[t2.document.slug, t2.id])

        assert not mail.outbox

    @mock.patch.object(Site.objects, 'get_current')
    def test_watch_forum_then_new_thread(self, get_current):
        """Watching a forum and creating a new thread should send email."""
        get_current.return_value.domain = 'testserver'

        u = user(save=True)
        d = document(title='an article title', save=True)
        f = self._toggle_watch_kbforum_as(u.username, d, turn_on=True)
        u2 = user(username='jsocol', save=True)
        self.client.login(username=u2.username, password='testpass')
        post(self.client, 'wiki.discuss.new_thread',
             {'title': 'a title', 'content': 'a post'}, args=[f.slug])

        t = Thread.objects.all().order_by('-id')[0]
        attrs_eq(mail.outbox[0], to=[u.email],
                 subject=u'an article title - a title')
        starts_with(mail.outbox[0].body, NEW_THREAD_EMAIL % (d.slug, t.id))

        self._toggle_watch_kbforum_as(u.username, d, turn_on=False)

    @mock.patch.object(Site.objects, 'get_current')
    def test_watch_forum_then_new_thread_as_self(self, get_current):
        """Watching a forum and creating a new thread as myself should not
        send email."""
        get_current.return_value.domain = 'testserver'

        u = user(save=True)
        d = document(save=True)
        f = self._toggle_watch_kbforum_as(u.username, d, turn_on=True)
        self.client.login(username=u.username, password='testpass')
        post(self.client, 'wiki.discuss.new_thread',
             {'title': 'a title', 'content': 'a post'}, args=[f.slug])
        # Assert no email is sent.
        assert not mail.outbox

    @mock.patch.object(Site.objects, 'get_current')
    def test_watch_forum_then_new_post(self, get_current):
        """Watching a forum and replying to a thread should send email."""
        get_current.return_value.domain = 'testserver'

        u = user(save=True)
        d = document(title='an article title', save=True)
        f = self._toggle_watch_kbforum_as(u.username, d, turn_on=True)
        t = thread(title='Sticky Thread', document=d, save=True)
        u2 = user(username='jsocol', save=True)
        self.client.login(username=u2.username, password='testpass')
        post(self.client, 'wiki.discuss.reply', {'content': 'a post'},
             args=[f.slug, t.id])

        p = Post.objects.all().order_by('-id')[0]
        attrs_eq(mail.outbox[0], to=[u.email],
                 subject='Re: an article title - Sticky Thread')
        starts_with(mail.outbox[0].body, REPLY_EMAIL % (d.slug, t.id, p.id))

    @mock.patch.object(Site.objects, 'get_current')
    def test_watch_forum_then_new_post_as_self(self, get_current):
        """Watching a forum and replying as myself should not send email."""
        get_current.return_value.domain = 'testserver'

        u = user(save=True)
        d = document(title='an article title', save=True)
        f = self._toggle_watch_kbforum_as(u.username, d, turn_on=True)
        t = thread(document=d, save=True)
        self.client.login(username=u.username, password='testpass')
        post(self.client, 'wiki.discuss.reply', {'content': 'a post'},
             args=[f.slug, t.id])
        # Assert no email is sent.
        assert not mail.outbox

    @mock.patch.object(Site.objects, 'get_current')
    def test_watch_both_then_new_post(self, get_current):
        """Watching both and replying to a thread should send ONE email."""
        get_current.return_value.domain = 'testserver'

        u = user(save=True)
        d = document(title='an article title', save=True)
        f = self._toggle_watch_kbforum_as(u.username, d, turn_on=True)
        t = thread(title='Sticky Thread', document=d, save=True)
        self._toggle_watch_thread_as(u.username, t, turn_on=True)
        u2 = user(username='jsocol', save=True)
        self.client.login(username=u2.username, password='testpass')
        post(self.client, 'wiki.discuss.reply', {'content': 'a post'},
             args=[f.slug, t.id])

        eq_(1, len(mail.outbox))
        p = Post.objects.all().order_by('-id')[0]
        attrs_eq(mail.outbox[0], to=[u.email],
                 subject='Re: an article title - Sticky Thread')
        starts_with(mail.outbox[0].body, REPLY_EMAIL % (d.slug, t.id, p.id))

        self._toggle_watch_kbforum_as(u.username, d, turn_on=False)
        self._toggle_watch_thread_as(u.username, t, turn_on=False)

    @mock.patch.object(Site.objects, 'get_current')
    def test_watch_locale_then_new_post(self, get_current):
        """Watching locale and reply to a thread."""
        get_current.return_value.domain = 'testserver'

        d = document(title='an article title', locale='en-US', save=True)
        t = thread(document=d, title='Sticky Thread', save=True)
        u = user(save=True)
        self.client.login(username=u.username, password='testpass')
        post(self.client, 'wiki.discuss.watch_locale', {'watch': 'yes'})

        # Reply as jsocol to document d.
        u2 = user(username='jsocol', save=True)
        self.client.login(username=u2.username, password='testpass')
        post(self.client, 'wiki.discuss.reply', {'content': 'a post'},
             args=[d.slug, t.id])

        # Email was sent as expected.
        eq_(1, len(mail.outbox))
        p = Post.objects.all().order_by('-id')[0]
        attrs_eq(mail.outbox[0], to=[u.email],
                 subject='Re: an article title - Sticky Thread')
        starts_with(mail.outbox[0].body, REPLY_EMAIL % (d.slug, t.id, p.id))

    @mock.patch.object(Site.objects, 'get_current')
    def test_watch_all_then_new_post(self, get_current):
        """Watching document + thread + locale and reply to thread."""
        get_current.return_value.domain = 'testserver'

        u = user(save=True)
        _d = document(title='an article title', save=True)
        d = self._toggle_watch_kbforum_as(u.username, _d, turn_on=True)
        t = thread(title='Sticky Thread', document=d, save=True)
        self._toggle_watch_thread_as(u.username, t, turn_on=True)
        self.client.login(username=u.username, password='testpass')
        post(self.client, 'wiki.discuss.watch_locale', {'watch': 'yes'})

        # Reply as jsocol to document d.
        u2 = user(username='jsocol', save=True)
        self.client.login(username=u2.username, password='testpass')
        post(self.client, 'wiki.discuss.reply', {'content': 'a post'},
             args=[d.slug, t.id])

        # Only ONE email was sent. As expected.
        eq_(1, len(mail.outbox))
        p = Post.objects.all().order_by('-id')[0]
        attrs_eq(mail.outbox[0], to=[u.email],
                 subject='Re: an article title - Sticky Thread')
        starts_with(mail.outbox[0].body, REPLY_EMAIL % (d.slug, t.id, p.id))

    @mock.patch.object(Site.objects, 'get_current')
    def test_watch_other_locale_then_new_thread(self, get_current):
        """Watching a different locale and createing a thread does not
        notify."""
        get_current.return_value.domain = 'testserver'

        d = document(locale='en-US', save=True)
        u = user(username='berkerpeksag', save=True)
        self.client.login(username=u.username, password='testpass')
        post(self.client, 'wiki.discuss.watch_locale', {'watch': 'yes'},
             locale='ja')

        u2 = user(save=True)
        self.client.login(username=u2.username, password='testpass')
        post(self.client, 'wiki.discuss.new_thread',
             {'title': 'a title', 'content': 'a post'}, args=[d.slug])

        # Email was not sent.
        eq_(0, len(mail.outbox))

    @mock.patch.object(Site.objects, 'get_current')
    def test_watch_locale_then_new_thread(self, get_current):
        """Watching locale and create a thread."""
        get_current.return_value.domain = 'testserver'

        d = document(title='an article title', locale='en-US', save=True)
        u = user(username='berkerpeksag', save=True)
        self.client.login(username=u.username, password='testpass')
        post(self.client, 'wiki.discuss.watch_locale', {'watch': 'yes'})

        u2 = user(username='jsocol', save=True)
        self.client.login(username=u2.username, password='testpass')
        post(self.client, 'wiki.discuss.new_thread',
             {'title': 'a title', 'content': 'a post'}, args=[d.slug])

        # Email was sent as expected.
        t = Thread.objects.all().order_by('-id')[0]
        attrs_eq(mail.outbox[0], to=[u.email],
                 subject=u'an article title - a title')
        starts_with(mail.outbox[0].body, NEW_THREAD_EMAIL % (d.slug, t.id))

    @mock.patch.object(Site.objects, 'get_current')
    def test_autowatch_new_thread(self, get_current):
        """Creating a new thread should email responses"""
        get_current.return_value.domain = 'testserver'

        d = document(save=True)
        u = user(save=True)
        self.client.login(username=u.username, password='testpass')
        s = Setting.objects.create(user=u, name='kbforums_watch_new_thread',
                                   value='False')
        data = {'title': 'a title', 'content': 'a post'}
        post(self.client, 'wiki.discuss.new_thread', data, args=[d.slug])

        t1 = thread(document=d, save=True)
        assert not NewPostEvent.is_notifying(u, t1), (
            'NewPostEvent should not be notifying.')

        s.value = 'True'
        s.save()
        post(self.client, 'wiki.discuss.new_thread', data, args=[d.slug])
        t2 = Thread.uncached.all().order_by('-id')[0]
        assert NewPostEvent.is_notifying(u, t2), (
            'NewPostEvent should be notifying')

    @mock.patch.object(Site.objects, 'get_current')
    def test_autowatch_reply(self, get_current):
        get_current.return_value.domain = 'testserver'

        u = user(save=True)
        t1 = thread(is_locked=False, save=True)
        t2 = thread(is_locked=False, save=True)
        assert not NewPostEvent.is_notifying(u, t1)
        assert not NewPostEvent.is_notifying(u, t2)

        self.client.login(username=u.username, password='testpass')
        s = Setting.objects.create(user=u,
                                   name='kbforums_watch_after_reply',
                                   value='True')
        data = {'content': 'some content'}
        post(self.client, 'wiki.discuss.reply', data,
             args=[t1.document.slug, t1.pk])
        assert NewPostEvent.is_notifying(u, t1)

        s.value = 'False'
        s.save()
        post(self.client, 'wiki.discuss.reply', data,
             args=[t2.document.slug, t2.pk])
        assert not NewPostEvent.is_notifying(u, t2)
