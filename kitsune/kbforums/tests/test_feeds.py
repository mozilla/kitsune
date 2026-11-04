import time
from unittest.mock import Mock

from django.contrib.auth.models import AnonymousUser
from django.http import Http404
from pyquery import PyQuery as pq

from kitsune.kbforums.feeds import PostsFeed, ThreadsFeed
from kitsune.kbforums.tests import PostFactory, ThreadFactory, get
from kitsune.sumo.tests import TestCase
from kitsune.users.tests import GroupFactory, UserFactory
from kitsune.wiki.tests import ApprovedRevisionFactory, AudienceFactory, DocumentFactory


class FeedSortingTestCase(TestCase):
    def test_threads_sort(self):
        """Ensure that threads are being sorted properly by date/time."""
        d = DocumentFactory()
        t = ThreadFactory(document=d)
        t.new_post(creator=t.creator, content="foo")
        time.sleep(1)
        t2 = ThreadFactory(document=d)
        t2.new_post(creator=t2.creator, content="foo")
        given_ = ThreadsFeed().items(d)[0].id
        self.assertEqual(t2.id, given_)

    def test_posts_sort(self):
        """Ensure that posts are being sorted properly by date/time."""
        t = ThreadFactory()
        t.new_post(creator=t.creator, content="foo")
        time.sleep(1)
        p2 = t.new_post(creator=t.creator, content="foo")
        given_ = PostsFeed().items(t)[0].id
        self.assertEqual(p2.id, given_)

    def test_multi_feed_titling(self):
        """Ensure that titles are being applied properly to feeds."""
        d = ApprovedRevisionFactory().document
        response = get(self.client, "wiki.discuss.threads", args=[d.slug])
        doc = pq(response.content)
        given_ = doc('link[type="application/atom+xml"]')[0].attrib["title"]
        exp_ = ThreadsFeed().title(d)
        self.assertEqual(exp_, given_)


class FeedRestrictedVisibilityTestCase(TestCase):
    """Test that feeds respect a document's restricted visibility."""

    def setUp(self):
        super().setUp()
        self.group = GroupFactory()
        self.restricted_doc = ApprovedRevisionFactory(
            document__allow_discussion=True,
            document__audiences=[AudienceFactory(groups=[self.group])],
        ).document
        self.thread = ThreadFactory(document=self.restricted_doc)
        PostFactory(thread=self.thread)

    def _mock_request(self, user):
        request = Mock()
        request.user = user
        request.LANGUAGE_CODE = self.restricted_doc.locale
        return request

    def test_threads_feed_anonymous_user(self):
        """Anonymous users can't access threads feed for restricted documents."""
        request = self._mock_request(AnonymousUser())
        with self.assertRaises(Http404):
            ThreadsFeed().get_object(request, self.restricted_doc.slug)

    def test_threads_feed_user_not_in_group(self):
        """Users not in the restricted group can't access threads feed."""
        request = self._mock_request(UserFactory())
        with self.assertRaises(Http404):
            ThreadsFeed().get_object(request, self.restricted_doc.slug)

    def test_threads_feed_user_in_group(self):
        """Users in the restricted group can access threads feed."""
        user = UserFactory(groups=[self.group])
        request = self._mock_request(user)
        doc = ThreadsFeed().get_object(request, self.restricted_doc.slug)
        self.assertEqual(doc, self.restricted_doc)

    def test_posts_feed_anonymous_user(self):
        """Anonymous users can't access posts feed for restricted documents."""
        request = self._mock_request(AnonymousUser())
        with self.assertRaises(Http404):
            PostsFeed().get_object(request, self.restricted_doc.slug, self.thread.id)

    def test_posts_feed_user_not_in_group(self):
        """Users not in the restricted group can't access posts feed."""
        request = self._mock_request(UserFactory())
        with self.assertRaises(Http404):
            PostsFeed().get_object(request, self.restricted_doc.slug, self.thread.id)

    def test_posts_feed_user_in_group(self):
        """Users in the restricted group can access posts feed."""
        user = UserFactory(groups=[self.group])
        request = self._mock_request(user)
        thread = PostsFeed().get_object(request, self.restricted_doc.slug, self.thread.id)
        self.assertEqual(thread, self.thread)
