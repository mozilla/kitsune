from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.core import mail

import mock
from nose.tools import eq_

from kbforums.events import NewPostEvent, NewThreadEvent
from kbforums.models import Thread, Post
from kbforums.tests import KBForumTestCase
from sumo.tests import post, attrs_eq, starts_with
from wiki.models import Document


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

https://testserver/en-US/kb/article-title/discuss/2#post-%s

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

https://testserver/en-US/kb/article-title/discuss/%s

--
Unsubscribe from these emails:
https://testserver/en-US/unsubscribe/"""


class NotificationsTests(KBForumTestCase):
    """Test that notifications get sent."""

    @mock.patch.object(NewPostEvent, 'fire')
    def test_fire_on_reply(self, fire):
        """The event fires when there is a reply."""
        t = Thread.objects.get(pk=2)
        self.client.login(username='jsocol', password='testpass')
        post(self.client, 'wiki.discuss.reply', {'content': 'a post'},
             args=[t.document.slug, t.id])
        # NewPostEvent.fire() is called.
        assert fire.called

    @mock.patch.object(NewThreadEvent, 'fire')
    def test_fire_on_new_thread(self, fire):
        """The event fires when there is a new thread."""
        d = Document.objects.get(pk=1)
        self.client.login(username='jsocol', password='testpass')
        post(self.client, 'wiki.discuss.new_thread',
             {'title': 'a title', 'content': 'a post'},
             args=[d.slug])
        # NewThreadEvent.fire() is called.
        assert fire.called

    def _toggle_watch_thread_as(self, username, turn_on=True, thread_id=2):
        """Watch a thread and return it."""
        thread = Thread.objects.get(pk=thread_id)
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

    def _toggle_watch_kbforum_as(self, username, turn_on=True, document_id=1):
        """Watch a discussion forum and return it."""
        document = Document.objects.get(pk=document_id)
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
            assert not NewPostEvent.is_notifying(user, document), (
                   'NewThreadEvent should not be notifying.')
        return document

    @mock.patch.object(Site.objects, 'get_current')
    def test_watch_thread_then_reply(self, get_current):
        """The event fires and sends emails when watching a thread."""
        get_current.return_value.domain = 'testserver'

        t = self._toggle_watch_thread_as('pcraciunoiu', turn_on=True)
        self.client.login(username='jsocol', password='testpass')
        post(self.client, 'wiki.discuss.reply', {'content': 'a post'},
             args=[t.document.slug, t.id])

        p = Post.objects.all().order_by('-id')[0]
        attrs_eq(mail.outbox[0], to=['user47963@nowhere'],
                 subject='Re: an article title - Sticky Thread')
        starts_with(mail.outbox[0].body, REPLY_EMAIL % p.id)

        self._toggle_watch_thread_as('pcraciunoiu', turn_on=False)

    def test_watch_other_thread_then_reply(self):
        """Watching a different thread than the one we're replying to shouldn't
        notify."""
        t = self._toggle_watch_thread_as('pcraciunoiu', turn_on=True)
        t2 = Thread.objects.exclude(pk=t.pk)[0]
        self.client.login(username='jsocol', password='testpass')
        post(self.client, 'wiki.discuss.reply', {'content': 'a post'},
             args=[t2.document.slug, t2.id])

        assert not mail.outbox

    @mock.patch.object(Site.objects, 'get_current')
    def test_watch_forum_then_new_thread(self, get_current):
        """Watching a forum and creating a new thread should send email."""
        get_current.return_value.domain = 'testserver'

        f = self._toggle_watch_kbforum_as('pcraciunoiu', turn_on=True)
        self.client.login(username='jsocol', password='testpass')
        post(self.client, 'wiki.discuss.new_thread',
             {'title': 'a title', 'content': 'a post'}, args=[f.slug])

        t = Thread.objects.all().order_by('-id')[0]
        attrs_eq(mail.outbox[0], to=['user47963@nowhere'],
                 subject=u'an article title - a title')
        starts_with(mail.outbox[0].body, NEW_THREAD_EMAIL % t.id)

        self._toggle_watch_kbforum_as('pcraciunoiu', turn_on=False)

    @mock.patch.object(Site.objects, 'get_current')
    def test_watch_forum_then_new_thread_as_self(self, get_current):
        """Watching a forum and creating a new thread as myself should not
        send email."""
        get_current.return_value.domain = 'testserver'

        f = self._toggle_watch_kbforum_as('pcraciunoiu', turn_on=True)
        self.client.login(username='pcraciunoiu', password='testpass')
        post(self.client, 'wiki.discuss.new_thread',
             {'title': 'a title', 'content': 'a post'}, args=[f.slug])
        # Assert no email is sent.
        assert not mail.outbox

    @mock.patch.object(Site.objects, 'get_current')
    def test_watch_forum_then_new_post(self, get_current):
        """Watching a forum and replying to a thread should send email."""
        get_current.return_value.domain = 'testserver'

        f = self._toggle_watch_kbforum_as('pcraciunoiu', turn_on=True)
        t = f.thread_set.all()[0]
        self.client.login(username='jsocol', password='testpass')
        post(self.client, 'wiki.discuss.reply', {'content': 'a post'},
             args=[f.slug, t.id])

        p = Post.objects.all().order_by('-id')[0]
        attrs_eq(mail.outbox[0], to=['user47963@nowhere'],
                 subject='Re: an article title - Sticky Thread')
        starts_with(mail.outbox[0].body, REPLY_EMAIL % p.id)

    @mock.patch.object(Site.objects, 'get_current')
    def test_watch_forum_then_new_post_as_self(self, get_current):
        """Watching a forum and replying as myself should not send email."""
        get_current.return_value.domain = 'testserver'

        f = self._toggle_watch_kbforum_as('pcraciunoiu', turn_on=True)
        t = f.thread_set.all()[0]
        self.client.login(username='pcraciunoiu', password='testpass')
        post(self.client, 'wiki.discuss.reply', {'content': 'a post'},
             args=[f.slug, t.id])
        # Assert no email is sent.
        assert not mail.outbox

    @mock.patch.object(Site.objects, 'get_current')
    def test_watch_both_then_new_post(self, get_current):
        """Watching both and replying to a thread should send ONE email."""
        get_current.return_value.domain = 'testserver'

        f = self._toggle_watch_kbforum_as('pcraciunoiu', turn_on=True)
        t = f.thread_set.all()[0]
        self._toggle_watch_thread_as('pcraciunoiu', turn_on=True,
                                     thread_id=t.id)
        self.client.login(username='jsocol', password='testpass')
        post(self.client, 'wiki.discuss.reply', {'content': 'a post'},
             args=[f.slug, t.id])

        eq_(1, len(mail.outbox))
        p = Post.objects.all().order_by('-id')[0]
        attrs_eq(mail.outbox[0], to=['user47963@nowhere'],
                 subject='Re: an article title - Sticky Thread')
        starts_with(mail.outbox[0].body, REPLY_EMAIL % p.id)

        self._toggle_watch_kbforum_as('pcraciunoiu', turn_on=False)
        self._toggle_watch_thread_as('pcraciunoiu', turn_on=False)

    @mock.patch.object(Site.objects, 'get_current')
    def test_watch_locale_then_new_post(self, get_current):
        """Watching locale and reply to a thread."""
        get_current.return_value.domain = 'testserver'

        d = Document.objects.filter(locale='en-US')[0]
        t = d.thread_set.all()[0]
        # Log in as pcraciunoiu.
        self.client.login(username='pcraciunoiu', password='testpass')
        post(self.client, 'wiki.discuss.watch_locale', {'watch': 'yes'})

        # Reply as jsocol to document d.
        self.client.login(username='jsocol', password='testpass')
        post(self.client, 'wiki.discuss.reply', {'content': 'a post'},
             args=[d.slug, t.id])

        # Email was sent as expected.
        eq_(1, len(mail.outbox))
        p = Post.objects.all().order_by('-id')[0]
        attrs_eq(mail.outbox[0], to=['user47963@nowhere'],
                 subject='Re: an article title - Sticky Thread')
        starts_with(mail.outbox[0].body, REPLY_EMAIL % p.id)

    @mock.patch.object(Site.objects, 'get_current')
    def test_watch_all_then_new_post(self, get_current):
        """Watching document + thread + locale and reply to thread."""
        get_current.return_value.domain = 'testserver'

        d = self._toggle_watch_kbforum_as('pcraciunoiu', turn_on=True)
        t = d.thread_set.all()[0]
        self._toggle_watch_thread_as('pcraciunoiu', turn_on=True,
                                     thread_id=t.id)
        # Log in as pcraciunoiu.
        self.client.login(username='pcraciunoiu', password='testpass')
        post(self.client, 'wiki.discuss.watch_locale', {'watch': 'yes'})

        # Reply as jsocol to document d.
        self.client.login(username='jsocol', password='testpass')
        post(self.client, 'wiki.discuss.reply', {'content': 'a post'},
             args=[d.slug, t.id])

        # Only ONE email was sent. As expected.
        eq_(1, len(mail.outbox))
        p = Post.objects.all().order_by('-id')[0]
        attrs_eq(mail.outbox[0], to=['user47963@nowhere'],
                 subject='Re: an article title - Sticky Thread')
        starts_with(mail.outbox[0].body, REPLY_EMAIL % p.id)

    @mock.patch.object(Site.objects, 'get_current')
    def test_watch_other_locale_then_new_thread(self, get_current):
        """Watching a different locale and createing a thread does not
        notify."""
        get_current.return_value.domain = 'testserver'

        d = Document.objects.filter(locale='en-US')[0]
        # Log in as pcraciunoiu.
        self.client.login(username='pcraciunoiu', password='testpass')
        post(self.client, 'wiki.discuss.watch_locale', {'watch': 'yes'},
             locale='ja')

        # Create new thread as jsocol for document d.
        self.client.login(username='jsocol', password='testpass')
        post(self.client, 'wiki.discuss.new_thread',
             {'title': 'a title', 'content': 'a post'}, args=[d.slug])

        # Email was not sent.
        eq_(0, len(mail.outbox))

    @mock.patch.object(Site.objects, 'get_current')
    def test_watch_locale_then_new_thread(self, get_current):
        """Watching locale and create a thread."""
        get_current.return_value.domain = 'testserver'

        d = Document.objects.filter(locale='en-US')[0]
        # Log in as pcraciunoiu.
        self.client.login(username='pcraciunoiu', password='testpass')
        post(self.client, 'wiki.discuss.watch_locale', {'watch': 'yes'})

        # Create new thread as jsocol for document d.
        self.client.login(username='jsocol', password='testpass')
        post(self.client, 'wiki.discuss.new_thread',
             {'title': 'a title', 'content': 'a post'}, args=[d.slug])

        # Email was sent as expected.
        t = Thread.objects.all().order_by('-id')[0]
        attrs_eq(mail.outbox[0], to=['user47963@nowhere'],
                 subject=u'an article title - a title')
        starts_with(mail.outbox[0].body, NEW_THREAD_EMAIL % t.id)
