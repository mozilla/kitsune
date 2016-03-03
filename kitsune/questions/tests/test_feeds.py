from datetime import datetime, timedelta

from django.core.cache import cache

from nose.tools import eq_
from pyquery import PyQuery as pq

from kitsune.sumo.urlresolvers import reverse
from kitsune.sumo.templatetags.jinja_helpers import urlparams
from kitsune.products.tests import ProductFactory, TopicFactory
from kitsune.questions.feeds import QuestionsFeed, TaggedQuestionsFeed
from kitsune.questions.models import Question
from kitsune.questions.tests import TestCaseBase, QuestionFactory
from kitsune.tags.tests import TagFactory
from kitsune.users.tests import UserFactory


class ForumTestFeeds(TestCaseBase):

    def test_tagged_feed(self):
        """Test the tagged feed."""
        t = TagFactory(name='green', slug='green')
        q = QuestionFactory()
        q.tags.add('green')
        items = TaggedQuestionsFeed().items(t)
        eq_(1, len(items))
        eq_(q.id, items[0].id)

        cache.clear()

        q = QuestionFactory()
        q.tags.add('green')
        q.updated = datetime.now() + timedelta(days=1)
        q.save()
        items = TaggedQuestionsFeed().items(t)
        eq_(2, len(items))
        eq_(q.id, items[0].id)

    def test_tagged_feed_link(self):
        """Make sure the tagged feed is discoverable on the questions page."""
        TagFactory(name='green', slug='green')
        url = urlparams(reverse('questions.list', args=['all']),
                        tagged='green')
        response = self.client.get(url)
        eq_(200, response.status_code)
        doc = pq(response.content)
        feed_links = doc('link[type="application/atom+xml"]')
        eq_(2, len(feed_links))
        eq_('Recently updated questions', feed_links[0].attrib['title'])
        eq_('/en-US/questions/feed?product=all', feed_links[0].attrib['href'])
        eq_('Recently updated questions tagged green',
            feed_links[1].attrib['title'])
        eq_('/en-US/questions/tagged/green/feed',
            feed_links[1].attrib['href'])

    def test_no_inactive_users(self):
        """Ensure that inactive users' questions don't appear in the feed."""
        u = UserFactory(is_active=False)

        q = Question(title='Test Question', content='Lorem Ipsum Dolor',
                     creator_id=u.id)
        q.save()
        assert q.id not in [x.id for x in QuestionsFeed().items({})]

    def test_question_feed_with_product(self):
        """Test that questions feeds with products work."""
        p = ProductFactory()
        url = reverse('questions.list', args=[p.slug])
        res = self.client.get(url)
        eq_(200, res.status_code)
        doc = pq(res.content)

        feed_links = doc('link[type="application/atom+xml"]')
        feed = feed_links[0]
        eq_(1, len(feed_links))
        eq_('Recently updated questions', feed.attrib['title'])
        eq_('/en-US/questions/feed?product=' + p.slug, feed.attrib['href'])
        eq_(200, self.client.get(feed.attrib['href']).status_code)

    def test_question_feed_with_product_and_topic(self):
        """Test that questions feeds with products and topics work."""
        p = ProductFactory()
        t = TopicFactory(product=p)
        url = urlparams(reverse('questions.list', args=[p.slug]), topic=t.slug)
        res = self.client.get(url)
        eq_(200, res.status_code)
        doc = pq(res.content)

        feed_links = doc('link[type="application/atom+xml"]')
        feed = feed_links[0]
        eq_(1, len(feed_links))
        eq_('Recently updated questions', feed.attrib['title'])
        eq_(urlparams('/en-US/questions/feed', product=p.slug, topic=t.slug),
            feed.attrib['href'])
        eq_(200, self.client.get(feed.attrib['href']).status_code)

    def test_question_feed_with_locale(self):
        """Test that questions feeds with products and topics work."""
        url = reverse('questions.list', args=['all'], locale='pt-BR')
        res = self.client.get(url)
        eq_(200, res.status_code)
        doc = pq(res.content)

        feed_links = doc('link[type="application/atom+xml"]')
        feed = feed_links[0]
        eq_(1, len(feed_links))
        eq_('Recently updated questions', feed.attrib['title'])
        eq_(urlparams('/pt-BR/questions/feed?product=all'),
            feed.attrib['href'])
        eq_(200, self.client.get(feed.attrib['href']).status_code)
