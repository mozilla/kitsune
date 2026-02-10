from datetime import timedelta

from django.core.cache import cache
from django.utils import timezone
from pyquery import PyQuery as pq

from kitsune.products.tests import ProductFactory, TopicFactory
from kitsune.questions.feeds import AnswersFeed, QuestionsFeed, TaggedQuestionsFeed
from kitsune.questions.models import Question
from kitsune.questions.tests import AnswerFactory, QuestionFactory
from kitsune.sumo.templatetags.jinja_helpers import urlparams
from kitsune.sumo.tests import TestCase
from kitsune.sumo.urlresolvers import reverse
from kitsune.tags.tests import TagFactory
from kitsune.users.tests import UserFactory


class ForumTestFeeds(TestCase):
    def test_tagged_feed(self):
        """Test the tagged feed."""
        t = TagFactory(name="green", slug="green")
        q = QuestionFactory()
        q.tags.add("green")
        items = TaggedQuestionsFeed().items(t)
        self.assertEqual(1, len(items))
        self.assertEqual(q.id, items[0].id)

        cache.clear()

        q = QuestionFactory()
        q.tags.add("green")
        q.updated = timezone.now() + timedelta(days=1)
        q.save()
        items = TaggedQuestionsFeed().items(t)
        self.assertEqual(2, len(items))
        self.assertEqual(q.id, items[0].id)

    def test_tagged_feed_link(self):
        """Make sure the tagged feed is discoverable on the questions page."""
        TagFactory(name="green", slug="green")
        url = urlparams(reverse("questions.list", args=["all"]), tagged="green")
        response = self.client.get(url)
        self.assertEqual(200, response.status_code)
        doc = pq(response.content)
        feed_links = doc('link[type="application/atom+xml"]')
        self.assertEqual(2, len(feed_links))
        self.assertEqual("Recently updated questions", feed_links[0].attrib["title"])
        self.assertEqual("/en-US/questions/feed?product=all", feed_links[0].attrib["href"])
        self.assertEqual("Recently updated questions tagged green", feed_links[1].attrib["title"])
        self.assertEqual("/en-US/questions/tagged/green/feed", feed_links[1].attrib["href"])

    def test_no_inactive_users(self):
        """Ensure that inactive users' questions don't appear in the feed."""
        u = UserFactory(is_active=False)

        q = Question(title="Test Question", content="Lorem Ipsum Dolor", creator_id=u.id)
        q.save()
        assert q.id not in [x.id for x in QuestionsFeed().items({})]

    def test_question_feed_with_product(self):
        """Test that questions feeds with products work."""
        p = ProductFactory()
        url = reverse("questions.list", args=[p.slug])
        res = self.client.get(url)
        self.assertEqual(200, res.status_code)
        doc = pq(res.content)

        feed_links = doc('link[type="application/atom+xml"]')
        feed = feed_links[0]
        self.assertEqual(1, len(feed_links))
        self.assertEqual("Recently updated questions", feed.attrib["title"])
        self.assertEqual("/en-US/questions/feed?product=" + p.slug, feed.attrib["href"])
        self.assertEqual(200, self.client.get(feed.attrib["href"]).status_code)

    def test_question_feed_with_product_and_topic(self):
        """Test that questions feeds with products and topics work."""
        p = ProductFactory()
        t = TopicFactory(products=[p])
        url = urlparams(reverse("questions.list", args=[p.slug]), topic=t.slug)
        res = self.client.get(url)
        self.assertEqual(200, res.status_code)
        doc = pq(res.content)

        feed_links = doc('link[type="application/atom+xml"]')
        feed = feed_links[0]
        self.assertEqual(1, len(feed_links))
        self.assertEqual("Recently updated questions", feed.attrib["title"])
        self.assertEqual(
            urlparams("/en-US/questions/feed", product=p.slug, topic=t.slug), feed.attrib["href"]
        )
        self.assertEqual(200, self.client.get(feed.attrib["href"]).status_code)

    def test_question_feed_with_locale(self):
        """Test that questions feeds with products and topics work."""
        url = reverse("questions.list", args=["all"], locale="pt-BR")
        res = self.client.get(url)
        self.assertEqual(200, res.status_code)
        doc = pq(res.content)

        feed_links = doc('link[type="application/atom+xml"]')
        feed = feed_links[0]
        self.assertEqual(1, len(feed_links))
        self.assertEqual("Perguntas atualizadas recentemente", feed.attrib["title"])
        self.assertEqual(urlparams("/pt-BR/questions/feed?product=all"), feed.attrib["href"])
        self.assertEqual(200, self.client.get(feed.attrib["href"]).status_code)

    def test_question_feed_with_control_characters(self):
        """Test that feeds properly handle control characters in titles/content."""
        u = UserFactory()
        q = Question(
            title="Test\x0bQuestion\x0cWith\x1fControl\x7fChars",
            content="Content\x0bwith\x0ccontrol\x1fchars",
            creator=u,
        )
        q.save()

        feed = QuestionsFeed()
        items = feed.items({})
        self.assertIn(q, items)

        item_title = feed.item_title(q)
        self.assertNotIn("\x0b", item_title)
        self.assertNotIn("\x0c", item_title)
        self.assertNotIn("\x1f", item_title)
        self.assertNotIn("\x7f", item_title)
        self.assertEqual("TestQuestionWithControlChars", item_title)

        item_description = feed.item_description(q)
        self.assertNotIn("\x0b", item_description)
        self.assertNotIn("\x0c", item_description)
        self.assertNotIn("\x1f", item_description)

        url = reverse("questions.feed")
        res = self.client.get(url)
        self.assertEqual(200, res.status_code)

    def test_answers_feed_with_control_characters(self):
        """Test that answer feeds properly handle control characters."""
        q = QuestionFactory(title="Question\x0bwith\x0ccontrol\x1fchars")
        a = AnswerFactory(
            question=q, content="Answer\x0bcontent\x0cwith\x1fcontrol\x7fchars", creator=q.creator
        )

        feed = AnswersFeed()
        feed_title = feed.title(q)
        self.assertNotIn("\x0b", feed_title)
        self.assertNotIn("\x0c", feed_title)
        self.assertNotIn("\x1f", feed_title)

        item_title = feed.item_title(a)
        self.assertNotIn("\x0b", item_title)
        self.assertNotIn("\x0c", item_title)
        self.assertNotIn("\x1f", item_title)
        self.assertNotIn("\x7f", item_title)

        item_description = feed.item_description(a)
        self.assertNotIn("\x0b", item_description)
        self.assertNotIn("\x0c", item_description)
        self.assertNotIn("\x1f", item_description)
        self.assertNotIn("\x7f", item_description)

        url = reverse("questions.answers.feed", args=[q.id])
        res = self.client.get(url)
        self.assertEqual(200, res.status_code)
