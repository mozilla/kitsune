from datetime import datetime, timedelta

from django.core.cache import cache

from nose.tools import eq_
from pyquery import PyQuery as pq

from kitsune.sumo.urlresolvers import reverse
from kitsune.sumo.helpers import urlparams
from kitsune.questions.feeds import QuestionsFeed, TaggedQuestionsFeed
from kitsune.questions.models import Question
from kitsune.questions.tests import TestCaseBase, question
from kitsune.tags.tests import tag
from kitsune.users.tests import user


class ForumTestFeedSorting(TestCaseBase):

    def test_tagged_feed(self):
        """Test the tagged feed."""
        t = tag(name='green', slug='green', save=True)
        q = question(save=True)
        q.tags.add('green')
        items = TaggedQuestionsFeed().items(t)
        eq_(1, len(items))
        eq_(q.id, items[0].id)

        cache.clear()

        q = question(save=True)
        q.tags.add('green')
        q.updated = datetime.now() + timedelta(days=1)
        q.save()
        items = TaggedQuestionsFeed().items(t)
        eq_(2, len(items))
        eq_(q.id, items[0].id)

    def test_tagged_feed_link(self):
        """Make sure the tagged feed is discoverable on the questions page."""
        tag(name='green', slug='green', save=True)
        url = urlparams(reverse('questions.questions'), tagged='green')
        response = self.client.get(url)
        doc = pq(response.content)
        feed_links = doc('link[type="application/atom+xml"]')
        eq_(2, len(feed_links))
        eq_('Recently updated questions', feed_links[0].attrib['title'])
        eq_('/en-US/questions/feed', feed_links[0].attrib['href'])
        eq_('Recently updated questions tagged green',
            feed_links[1].attrib['title'])
        eq_('/en-US/questions/tagged/green/feed',
            feed_links[1].attrib['href'])

    def test_no_inactive_users(self):
        """Ensure that inactive users' questions don't appear in the feed."""
        u = user(is_active=False, save=True)

        q = Question(title='Test Question', content='Lorem Ipsum Dolor',
                     creator_id=u.id)
        q.save()
        assert q.id not in [x.id for x in QuestionsFeed().items()]
