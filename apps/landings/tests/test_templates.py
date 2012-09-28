import mock
import waffle
from nose.tools import eq_
from pyquery import PyQuery as pq

from products.tests import product
from search.tests.test_es import ElasticTestCase
from sumo.tests import TestCase
from sumo.urlresolvers import reverse
from topics.models import HOT_TOPIC_SLUG
from topics.tests import topic
from wiki.tests import document, revision


class HomeTestCase(ElasticTestCase):
    def test_home(self):
        """Verify that home page renders topics and products."""

        # Create some topics and products
        topic(slug=HOT_TOPIC_SLUG, save=True)
        for i in range(6):
            topic(save=True)
        for i in range(4):
            product(save=True)

        # GET the home page and verify the content
        r = self.client.get(reverse('home'), follow=True)
        eq_(200, r.status_code)
        doc = pq(r.content)
        eq_(6, len(doc('#help-topics li')))
        eq_(5, len(doc('#products-and-services li')))

    def test_hot_topics(self):
        """Verifies the hot topics section."""
        # Create the hot topics topic.
        hot = topic(slug=HOT_TOPIC_SLUG, save=True)

        # Create 3 hot documents.
        for i in range(3):
            doc = revision(is_approved=True, save=True).document
            doc.topics.add(hot)

        # Create a not hot document.
        doc = revision(is_approved=True, save=True).document

        self.refresh()

        # GET the home page and verify the content
        r = self.client.get(reverse('home'), follow=True)
        eq_(200, r.status_code)
        doc = pq(r.content)
        eq_(3, len(doc('#hot-topics li')))

    def test_mozilla_news(self):
        """Verifies the Mozilla News section."""
        # If "Mozilla News" article doesn't exist, home page
        # should still work and omit the section.
        r = self.client.get(reverse('home'), follow=True)
        eq_(200, r.status_code)
        doc = pq(r.content)
        eq_(len(doc('#mozilla-news')), 0)

        # Create the "Mozilla News" article and verify it on home page.
        d = document(title='Mozilla News', slug='mozilla-news', save=True)
        rev = revision(
            document=d, content='splendid', is_approved=True, save=True)
        d.current_revision = rev
        d.save()
        r = self.client.get(reverse('home'), follow=True)
        eq_(200, r.status_code)
        doc = pq(r.content)
        moz_news = doc('#mozilla-news')
        eq_(len(moz_news), 1)
        assert 'splendid' in moz_news.text()
