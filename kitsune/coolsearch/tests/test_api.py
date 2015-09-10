import json

from nose.tools import eq_

from kitsune.forums.tests import post, thread
from kitsune.questions.tests import question
from kitsune.products.tests import product, topic
from kitsune.search.tests.test_es import ElasticTestCase
from kitsune.sumo.urlresolvers import reverse
from kitsune.wiki.tests import document, revision


class SearchApiTests(ElasticTestCase):

    def test_wiki_search(self):
        """Test searching for wiki documents."""
        p1 = product(title=u'Product One', slug='product-one', save=True)
        p2 = product(title=u'Product Two', slug='product-two', save=True)

        t1 = topic(slug='doesnotexist', save=True)
        t2 = topic(slug='extant', save=True)
        t3 = topic(slug='tagged', save=True)

        doc = document(
            title=u'help plz',
            category=10,
            save=True,
        )
        doc.products.add(p1)
        doc.topics.add(t2)
        revision(document=doc, is_approved=True, save=True)

        doc = document(
            title=u'I can get no firefox',
            category=10,
            save=True,
        )
        doc.products.add(p1)
        doc.products.add(p2)
        doc.topics.add(t3)
        revision(document=doc, is_approved=True, save=True)

        doc = document(
            title=u'firefox help',
            category=30,
            save=True,
        )
        doc.products.add(p2)
        doc.topics.add(t2)
        doc.topics.add(t3)
        revision(document=doc, is_approved=True, save=True)

        self.refresh()

        url = reverse('coolsearch.search_wiki')

        # ---------------------------------------------------------------------
        # All results.
        response = self.client.get(url, {})
        eq_(200, response.status_code)
        content = json.loads(response.content)
        eq_(content['num_results'], 3)

        # ---------------------------------------------------------------------
        # Testing query filter.
        response = self.client.get(url, {
            'query': 'help',
        })
        eq_(200, response.status_code)
        content = json.loads(response.content)
        eq_(content['num_results'], 2)

        response = self.client.get(url, {
            'query': 'firefox',
        })
        eq_(200, response.status_code)
        content = json.loads(response.content)
        eq_(content['num_results'], 2)

        # ---------------------------------------------------------------------
        # Testing category filter.
        response = self.client.get(url, {
            'category': 30,
        })
        eq_(200, response.status_code)
        content = json.loads(response.content)
        eq_(content['num_results'], 1)

        response = self.client.get(url, {
            'category': [10, 30],
        })
        eq_(200, response.status_code)
        content = json.loads(response.content)
        eq_(content['num_results'], 3)

        response = self.client.get(url, {
            'category': [20],
        })
        eq_(200, response.status_code)
        content = json.loads(response.content)
        eq_(content['num_results'], 0)

        # ---------------------------------------------------------------------
        # Testing product filter.
        response = self.client.get(url, {
            'product': [p1.slug],
        })
        eq_(200, response.status_code)
        content = json.loads(response.content)
        eq_(content['num_results'], 2)

        response = self.client.get(url, {
            'product': [p2.slug],
        })
        eq_(200, response.status_code)
        content = json.loads(response.content)
        eq_(content['num_results'], 2)

        response = self.client.get(url, {
            'product': [p1.slug, p2.slug],
        })
        eq_(200, response.status_code)
        content = json.loads(response.content)
        eq_(content['num_results'], 1)

        # ---------------------------------------------------------------------
        # Testing topics filter.
        response = self.client.get(url, {
            'topics': [t2.slug],
        })
        eq_(200, response.status_code)
        content = json.loads(response.content)
        eq_(content['num_results'], 2)

        response = self.client.get(url, {
            'topics': [t3.slug],
        })
        eq_(200, response.status_code)
        content = json.loads(response.content)
        eq_(content['num_results'], 2)

        response = self.client.get(url, {
            'topics': [t2.slug, t3.slug],
        })
        eq_(200, response.status_code)
        content = json.loads(response.content)
        eq_(content['num_results'], 1)

        response = self.client.get(url, {
            'topics': [t1.slug],
        })
        eq_(200, response.status_code)
        content = json.loads(response.content)
        eq_(content['num_results'], 0)

    def test_question_search(self):
        """Tests searching for questions."""
        p1 = product(title=u'Product One', slug='product-one', save=True)
        p2 = product(title=u'Product Two', slug='product-two', save=True)

        t1 = topic(slug='doesnotexist', save=True)
        t2 = topic(slug='extant', save=True)
        t3 = topic(slug='tagged', save=True)

        question(
            title=u'audio',
            product=p1,
            topic=t2,
            save=True,
        )
        question(
            title=u'something something',
            product=p1,
            topic=t3,
            save=True,
        )
        question(
            title=u'why so serious',
            product=p2,
            topic=t2,
            save=True,
        )

        self.refresh()

        # ---------------------------------------------------------------------
        # Testing query filter.
        url = reverse('coolsearch.search_question')

        response = self.client.get(url, {
            'query': 'audio',
        })
        eq_(200, response.status_code)
        content = json.loads(response.content)
        eq_(content['num_results'], 1)

        # ---------------------------------------------------------------------
        # Testing product filter.
        response = self.client.get(url, {
            'product': [p1.slug],
        })
        eq_(200, response.status_code)
        content = json.loads(response.content)
        eq_(content['num_results'], 2)

        response = self.client.get(url, {
            'product': [p2.slug],
        })
        eq_(200, response.status_code)
        content = json.loads(response.content)
        eq_(content['num_results'], 1)

        # ---------------------------------------------------------------------
        # Testing topics filter.
        response = self.client.get(url, {
            'topics': [t2.slug],
        })
        eq_(200, response.status_code)
        content = json.loads(response.content)
        eq_(content['num_results'], 2)

        response = self.client.get(url, {
            'topics': [t3.slug],
        })
        eq_(200, response.status_code)
        content = json.loads(response.content)
        eq_(content['num_results'], 1)

        response = self.client.get(url, {
            'topics': [t1.slug],
        })
        eq_(200, response.status_code)
        content = json.loads(response.content)
        eq_(content['num_results'], 0)

    def test_forum_search(self):
        """Test searching for forum threads."""
        thread1 = thread(title=u'crash', save=True)
        post(thread=thread1, save=True)

        self.refresh()

        response = self.client.get(reverse('coolsearch.search_forum'), {
            'query': 'crash',
        })
        eq_(200, response.status_code)
        content = json.loads(response.content)
        eq_(content['num_results'], 1)
