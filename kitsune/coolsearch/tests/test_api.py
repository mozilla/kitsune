import json

from nose.tools import eq_

from kitsune.forums.tests import post, thread
from kitsune.questions.tests import question
from kitsune.search.tests.test_es import ElasticTestCase
from kitsune.sumo.urlresolvers import reverse
from kitsune.wiki.tests import document, revision


class SearchApiTests(ElasticTestCase):

    def test_wiki_search(self):
        """Test searching for wiki documents."""
        doc = document(
            title=u'help plz',
            category=10,
            save=True,
        )
        revision(document=doc, is_approved=True, save=True)

        doc = document(
            title=u'I can get no firefox',
            category=10,
            save=True,
        )
        revision(document=doc, is_approved=True, save=True)

        doc = document(
            title=u'firefox help',
            category=10,
            save=True,
        )
        revision(document=doc, is_approved=True, save=True)

        self.refresh()

        url = reverse('coolsearch.search_wiki')

        # All results.
        response = self.client.get(url, {})
        eq_(200, response.status_code)

        content = json.loads(response.content)
        eq_(content['num_results'], 3)

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

    def test_question_search(self):
        """Tests searching for questions."""
        ques = question(title=u'audio', save=True)
        ques.tags.add(u'Windows 7')

        self.refresh()

        response = self.client.get(reverse('coolsearch.search_question'), {
            'query': 'audio',
        })

        eq_(200, response.status_code)

        content = json.loads(response.content)
        eq_(content['num_results'], 1)
