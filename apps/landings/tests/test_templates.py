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


class MobileHomeTestCase(TestCase):
    def test_top_text(self):
        response = self.client.get(reverse('home.mobile'), follow=True)
        self.assertContains(response, 'Firefox for Mobile')

    def test_no_plugin_check(self):
        response = self.client.get(reverse('home.mobile'), follow=True)
        self.assertNotContains(response, 'run an instant check')

    def test_search_params(self):
        response = self.client.get(reverse('home.mobile'), follow=True)
        doc = pq(response.content)
        eq_('mobile',
            doc('#support-search input[name="q_tags"]')[0].attrib['value'])
        eq_('mobile',
            doc('#support-search input[name="product"]')[0].attrib['value'])


class HomeTestCase(ElasticTestCase):
    @mock.patch.object(waffle, 'flag_is_active')
    def test_home(self, flag_is_active):
        """Verify that home page renders topics and products."""
        flag_is_active.return_value = True

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

    @mock.patch.object(waffle, 'flag_is_active')
    def test_hot_topics(self, flag_is_active):
        """Verifies the hot topics section."""
        flag_is_active.return_value = True

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

    @mock.patch.object(waffle, 'flag_is_active')
    def test_mozilla_news(self, flag_is_active):
        """Verifies the Mozilla News section."""
        flag_is_active.return_value = True

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
