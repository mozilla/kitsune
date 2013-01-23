from nose.tools import eq_

from kbforums.models import Thread
from kbforums.tests import KBForumTestCase, thread
from kbforums.events import NewThreadEvent, NewPostEvent
from sumo.tests import get, post
from sumo.urlresolvers import reverse
from users.tests import user, add_permission
from wiki.tests import document


class ThreadAuthorityPermissionsTests(KBForumTestCase):
    """Test thread views authority permissions."""

    def setUp(self):
        self.u = user(save=True)

    def test_new_thread_without_view_permission(self):
        """Making a new thread without view permission should 404."""
        self.client.login(username=self.u.username, password='testpass')
        response = post(self.client, 'wiki.discuss.new_thread',
                        {'title': 'Blahs', 'content': 'Blahs'},
                        args=['restricted-forum'])
        eq_(404, response.status_code)

    def test_watch_GET_405(self):
        """Watch forum with HTTP GET results in 405."""
        self.client.login(username=self.u.username, password='testpass')
        d = document(save=True)
        response = get(self.client, 'wiki.discuss.watch_forum', args=[d.slug])
        eq_(405, response.status_code)

    def test_watch_forum_without_permission(self):
        """Watching forums without the view_in_forum permission should 404."""
        self.client.login(username=self.u.username, password='testpass')
        response = self.client.post(reverse('wiki.discuss.watch_forum',
                                            args=['restricted-forum']),
                                    {'watch': 'yes'}, follow=False)
        eq_(404, response.status_code)

    def test_watch_thread_without_permission(self):
        """Watching threads without the view_in_forum permission should 404."""
        self.client.login(username=self.u.username, password='testpass')
        response = self.client.post(reverse('wiki.discuss.watch_thread',
                                            args=['restricted-forum', 6]),
                                    {'watch': 'yes'}, follow=False)
        eq_(404, response.status_code)

    def test_read_without_permission(self):
        """Listing threads without the view_in_forum permission should 404."""
        response = get(self.client, 'wiki.discuss.threads',
                       args=['restricted-forum'])
        eq_(404, response.status_code)


class ThreadTests(KBForumTestCase):
    """Test thread views."""

    def test_watch_forum(self):
        """Watch then unwatch a forum."""
        u = user(save=True)
        self.client.login(username=u.username, password='testpass')

        d = document(save=True)
        post(self.client, 'wiki.discuss.watch_forum', {'watch': 'yes'},
             args=[d.slug])
        assert NewThreadEvent.is_notifying(u, d)
        # NewPostEvent is not notifying.
        t = thread(document=d, save=True)
        p = t.new_post(creator=t.creator, content='test')
        #p = d.thread_set.all()[0].post_set.all()[0]
        assert not NewPostEvent.is_notifying(u, p)

        post(self.client, 'wiki.discuss.watch_forum', {'watch': 'no'},
             args=[d.slug])
        assert not NewThreadEvent.is_notifying(u, d)

    def test_watch_thread(self):
        """Watch then unwatch a thread."""
        u = user(save=True)
        self.client.login(username=u.username, password='testpass')

        t = thread(save=True)
        post(self.client, 'wiki.discuss.watch_thread', {'watch': 'yes'},
             args=[t.document.slug, t.id])
        assert NewPostEvent.is_notifying(u, t)
        # NewThreadEvent is not notifying.
        assert not NewThreadEvent.is_notifying(u, t.document)

        post(self.client, 'wiki.discuss.watch_thread', {'watch': 'no'},
             args=[t.document.slug, t.id])
        assert not NewPostEvent.is_notifying(u, t)

    def test_edit_thread(self):
        """Changing thread title works."""
        u = user(save=True)
        self.client.login(username=u.username, password='testpass')

        d = document(save=True)
        t = thread(title='Sticky Thread', document=d, creator=u, save=True)
        post(self.client, 'wiki.discuss.edit_thread', {'title': 'A new title'},
             args=[d.slug, t.id])
        edited_t = d.thread_set.get(pk=t.id)

        eq_('Sticky Thread', t.title)
        eq_('A new title', edited_t.title)

    def test_edit_thread_moderator(self):
        """Editing post as a moderator works."""
        u = user(save=True)
        add_permission(u, Thread, 'change_thread')
        t = thread(title='Sticky Thread', save=True)
        d = t.document
        self.client.login(username=u.username, password='testpass')

        eq_('Sticky Thread', t.title)

        r = post(self.client, 'wiki.discuss.edit_thread',
                 {'title': 'new title'}, args=[d.slug, t.id])
        eq_(200, r.status_code)

        edited_t = Thread.uncached.get(pk=t.id)
        eq_('new title', edited_t.title)

    def test_disallowed_404(self):
        """If document.allow_discussion is false, should return 404."""
        u = user(username='berkerpeksag', save=True)
        self.client.login(username=u.username, password='testpass')
        doc = document(allow_discussion=False, save=True)

        def check(url):
            response = get(self.client, url, args=[doc.slug])
            st = response.status_code
            eq_(404, st, '%s was %s, not 404' % (url, st))
        check('wiki.discuss.threads')
        check('wiki.discuss.new_thread')
        check('wiki.discuss.threads.feed')


class ThreadPermissionsTests(KBForumTestCase):

    def setUp(self):
        super(ThreadPermissionsTests, self).setUp()
        self.doc = document(save=True)
        self.u = user(save=True)
        self.thread = thread(document=self.doc, creator=self.u, save=True)
        self.post = self.thread.new_post(creator=self.thread.creator,
                                         content='foo')
        # Login for testing 403s
        u2 = user(save=True)
        self.client.login(username=u2.username, password='testpass')

    def tearDown(self):
        self.client.logout()
        super(ThreadPermissionsTests, self).tearDown()

    def test_edit_thread_403(self):
        """Editing a thread without permissions returns 403."""
        response = get(self.client, 'wiki.discuss.edit_thread',
                       args=[self.doc.slug, self.thread.id])
        eq_(403, response.status_code)

    def test_edit_locked_thread_403(self):
        """Editing a locked thread returns 403."""
        t = thread(document=self.doc, creator=self.u, is_locked=True,
                   save=True)
        response = get(self.client, 'wiki.discuss.edit_thread',
                       args=[self.doc.slug, t.id])
        eq_(403, response.status_code)

    def test_delete_thread_403(self):
        """Deleting a thread without permissions returns 403."""
        response = get(self.client, 'wiki.discuss.delete_thread',
                       args=[self.doc.slug, self.thread.id])
        eq_(403, response.status_code)

    def test_sticky_thread_405(self):
        """Marking a thread sticky with a HTTP GET returns 405."""
        response = get(self.client, 'wiki.discuss.sticky_thread',
                       args=[self.doc.slug, self.thread.id])
        eq_(405, response.status_code)

    def test_sticky_thread_403(self):
        """Marking a thread sticky without permissions returns 403."""
        response = post(self.client, 'wiki.discuss.sticky_thread',
                        args=[self.doc.slug, self.thread.id])
        eq_(403, response.status_code)

    def test_locked_thread_403(self):
        """Marking a thread locked without permissions returns 403."""
        response = post(self.client, 'wiki.discuss.lock_thread',
                        args=[self.doc.slug, self.thread.id])
        eq_(403, response.status_code)

    def test_locked_thread_405(self):
        """Marking a thread locked via a GET instead of a POST request."""
        response = get(self.client, 'wiki.discuss.lock_thread',
                       args=[self.doc.slug, self.thread.id])
        eq_(405, response.status_code)

    def test_post_edit_403(self):
        """Editing a post without permissions returns 403."""
        response = get(self.client, 'wiki.discuss.edit_post',
                       args=[self.doc.slug, self.thread.id, self.post.id])
        eq_(403, response.status_code)

    def test_post_delete_403(self):
        """Deleting a post without permissions returns 403."""
        response = get(self.client, 'wiki.discuss.delete_post',
                       args=[self.doc.slug, self.thread.id, self.post.id])
        eq_(403, response.status_code)
