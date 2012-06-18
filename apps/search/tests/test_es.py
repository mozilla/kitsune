import json
import datetime

import mock
from django.conf import settings
from elasticutils import get_es
from nose import SkipTest
from nose.tools import eq_
from test_utils import TestCase

from forums.tests import thread, post
from questions.tests import question, answer, answervote, questionvote
from questions.models import Question
from search.models import generate_tasks
from search import es_utils
from sumo.tests import LocalizingClient
from sumo.urlresolvers import reverse
from waffle.models import Flag
from wiki.tests import document, revision


class ElasticTestCase(TestCase):
    """Base class for Elastic Search tests, providing some conveniences"""
    skipme = False

    @classmethod
    def setUpClass(cls):
        super(ElasticTestCase, cls).setUpClass()

        if not getattr(settings, 'ES_HOSTS'):
            cls.skipme = True
            return

        # try to connect to ES and if it fails, skip ElasticTestCases.
        import pyes.urllib3
        import pyes.exceptions
        try:
            get_es().collect_info()
        except pyes.urllib3.MaxRetryError:
            cls.skipme = True
            return

        # Swap out for better versions.
        cls._old_read_index = es_utils.READ_INDEX
        cls._old_write_index = es_utils.WRITE_INDEX
        es_utils.READ_INDEX = u'sumo_test'
        es_utils.WRITE_INDEX = u'sumo_test'

    @classmethod
    def tearDownClass(cls):
        if not cls.skipme:
            # Restore old settings.
            es_utils.READ_INDEX = cls._old_read_index
            es_utils.WRITE_INDEX = cls._old_write_index

    def setUp(self):
        if self.skipme:
            raise SkipTest

        super(ElasticTestCase, self).setUp()
        Flag.objects.create(name='elasticsearch', everyone=True)
        self.setup_indexes()

    def tearDown(self):
        super(ElasticTestCase, self).tearDown()
        self.teardown_indexes()

    def refresh(self, timesleep=0):
        index = es_utils.WRITE_INDEX

        # Any time we're doing a refresh, we're making sure that the
        # index is ready to be queried.  Given that, it's almost
        # always the case that we want to run all the generated tasks,
        # then refresh.
        generate_tasks()

        get_es().refresh(index, timesleep=timesleep)

    def setup_indexes(self):
        """(Re-)create ES indexes."""
        from search.es_utils import es_reindex_cmd

        # This removes the previous round of indexes and creates new
        # ones with mappings and all that.
        es_reindex_cmd(delete=True)

        # TODO: This is kind of bad.  If setup_indexes gets called in
        # a setUp and that setUp at some point throws an exception, we
        # could end up in a situation where setUp throws an exception,
        # so tearDown doesn't get called and we never set
        # ES_LIVE_INDEXING to False and thus ES_LIVE_INDEXING is True
        # for a bunch of tests it shouldn't be true for.
        #
        # For settings like this, it's better to mock it in the class
        # because the mock will set it back regardless of whether the
        # test fails.
        settings.ES_LIVE_INDEXING = True

    def teardown_indexes(self):
        es = get_es()
        es.delete_index_if_exists(es_utils.READ_INDEX)

        settings.ES_LIVE_INDEXING = False


class ElasticSearchTasksTests(ElasticTestCase):
    @mock.patch.object(Question, 'index')
    def test_tasks(self, index_fun):
        """Tests to make sure tasks are added and run"""

        q = question()
        # Don't call self.refresh here since that calls generate_tasks().

        eq_(index_fun.call_count, 0)

        q.save()
        generate_tasks()

        eq_(index_fun.call_count, 1)

    @mock.patch.object(Question, 'index')
    def test_tasks_squashed(self, index_fun):
        """Tests to make sure tasks are squashed"""

        q = question()
        # Don't call self.refresh here since that calls generate_tasks().

        eq_(index_fun.call_count, 0)

        q.save()
        q.save()
        q.save()
        q.save()

        eq_(index_fun.call_count, 0)

        generate_tasks()

        eq_(index_fun.call_count, 1)


class ElasticSearchViewPagingTests(ElasticTestCase):
    client_class = LocalizingClient

    def test_front_page_search_paging(self):
        # Create 30 documents
        for i in range(30):
            doc = document(
                title=u'How to fix your audio %d' % i,
                locale=u'en-US',
                category=10,
                save=True)
            doc.tags.add(u'desktop')
            revision(document=doc, is_approved=True, save=True)

        # Create 20 questions
        for i in range(20):
            ques = question(title=u'audio',  content=u'audio bad.', save=True)
            ques.tags.add(u'desktop')
            ans = answer(question=ques, save=True)
            answervote(answer=ans, helpful=True, save=True)

        self.refresh()

        response = self.client.get(reverse('search'), {
            'q_tags': 'desktop', 'product': 'desktop', 'q': 'audio',
            'format': 'json'
        })
        eq_(200, response.status_code)
        content = json.loads(response.content)

        # Make sure there are 20 results.
        eq_(content['total'], 20)

        # Make sure only 10 of them are kb.
        docs = [mem for mem in content['results']
                if mem['type'] == 'document']
        eq_(len(docs), 10)


class ElasticSearchViewTests(ElasticTestCase):
    client_class = LocalizingClient

    def test_front_page_search_for_questions(self):
        """This tests whether doing a search from the front page returns
        question results.

        Bug #709202.

        """
        # Create a question with an answer with an answervote that
        # marks the answer as helpful.  The question should have the
        # "desktop" tag.
        ques = question(
            title=u'audio fails',
            content=u'my audio dont work.')
        ques.save()

        ques.tags.add(u'desktop')

        ans = answer(
            question=ques,
            content=u'You need to turn your volume up.')
        ans.save()

        ansvote = answervote(
            answer=ans,
            helpful=True)
        ansvote.save()

        self.refresh()

        # This is the search that you get when you start on the sumo
        # homepage and do a search from the box with two differences:
        # first, we do it in json since it's easier to deal with
        # testing-wise and second, we search for 'audio' since we have
        # data for that.
        response = self.client.get(reverse('search'), {
            'q_tags': 'desktop', 'product': 'desktop', 'q': 'audio',
            'format': 'json'
        })

        eq_(200, response.status_code)

        content = json.loads(response.content)
        eq_(content['total'], 1)

        # This is another search that picks up results based on the
        # answer_content.  answer_content is in a string array, so
        # this makes sure that works.
        response = self.client.get(reverse('search'), {
            'q_tags': 'desktop', 'product': 'desktop', 'q': 'volume',
            'format': 'json'
        })

        eq_(200, response.status_code)

        content = json.loads(response.content)
        eq_(content['total'], 1)

    def test_front_page_search_for_wiki(self):
        """This tests whether doing a search from the front page returns
        wiki document results.

        Bug #709202.

        """
        doc = document(
            title=u'How to fix your audio',
            locale=u'en-US',
            category=10)
        doc.save()

        doc.tags.add(u'desktop')

        rev = revision(
            document=doc,
            summary=u'Volume.',
            content=u'Turn up the volume.',
            is_approved=True)
        rev.save()

        self.refresh()

        # This is the search that you get when you start on the sumo
        # homepage and do a search from the box with two differences:
        # first, we do it in json since it's easier to deal with
        # testing-wise and second, we search for 'audio' since we have
        # data for that.
        response = self.client.get(reverse('search'), {
            'q_tags': 'desktop', 'product': 'desktop', 'q': 'audio',
            'format': 'json'
        })

        eq_(200, response.status_code)

        content = json.loads(response.content)
        eq_(content['total'], 1)

    def test_advanced_search_for_wiki_no_query(self):
        """Tests advanced search with no query"""
        doc = document(
            title=u'How to fix your audio',
            locale=u'en-US',
            category=10)
        doc.save()

        doc.tags.add(u'desktop')

        rev = revision(
            document=doc,
            summary=u'Volume.',
            content=u'Turn up the volume.',
            is_approved=True)
        rev.save()

        self.refresh()

        # This is the search that you get when you start on the sumo
        # homepage and do a search from the box with two differences:
        # first, we do it in json since it's easier to deal with
        # testing-wise and second, we search for 'audio' since we have
        # data for that.
        response = self.client.get(reverse('search'), {
            'q': '', 'tags': 'desktop', 'w': '1', 'a': '1',
            'format': 'json'
        })

        eq_(200, response.status_code)

        content = json.loads(response.content)
        eq_(content['total'], 1)

    def test_advanced_search_questions_sortby(self):
        """Tests advanced search for questions with a sortby"""
        question(title=u'tags tags tags', save=True)

        self.refresh()

        # Advanced search for questions with sortby set to 3 which is
        # '-replies' which is different between Sphinx and ES.
        response = self.client.get(reverse('search'), {
            'q': '', 'tags': 'desktop', 'w': '2', 'a': '1', 'sortby': '3',
            'format': 'json'
        })

        eq_(200, response.status_code)

        content = json.loads(response.content)
        eq_(content['total'], 1)

    def test_advanced_search_questions_num_votes(self):
        """Tests advanced search for questions num_votes filter"""
        q = question(title=u'tags tags tags', save=True)

        # Add two question votes
        questionvote(question=q, save=True)
        questionvote(question=q, save=True)

        self.refresh()

        # Advanced search for questions with num_votes > 5. The above
        # question should be not in this set.
        response = self.client.get(reverse('search'), {
            'q': '', 'tags': 'desktop', 'w': '2', 'a': '1',
            'num_voted': 2, 'num_votes': 5,
            'format': 'json'
        })

        eq_(200, response.status_code)

        content = json.loads(response.content)
        eq_(content['total'], 0)

        # Advanced search for questions with num_votes < 1. The above
        # question should be not in this set.
        response = self.client.get(reverse('search'), {
            'q': '', 'tags': 'desktop', 'w': '2', 'a': '1',
            'num_voted': 1, 'num_votes': 1,
            'format': 'json'
        })

        eq_(200, response.status_code)

        content = json.loads(response.content)
        eq_(content['total'], 0)

    def test_forums_search(self):
        """This tests whether forum posts show up in searches."""
        thread1 = thread(
            title=u'Why don\'t we spell crash backwards?')
        thread1.save()

        post1 = post(
            thread=thread1,
            content=u'What, like hsarc?  That\'s silly.')
        post1.save()

        self.refresh()

        response = self.client.get(reverse('search'), {
            'author': '', 'created': '0', 'created_date': '',
            'updated': '0', 'updated_date': '', 'sortby': '0',
            'a': '1', 'w': '4', 'q': 'hsarc',
            'format': 'json'
        })

        eq_(200, response.status_code)

        content = json.loads(response.content)
        eq_(content['total'], 1)

    def test_forums_thread_created(self):
        post_created_ds = datetime.datetime(2010, 1, 1, 12, 00)
        thread1 = thread(
            title=u'Why don\'t we spell crash backwards?',
            created=post_created_ds)
        thread1.save()

        post1 = post(
            thread=thread1,
            content=u'What, like hsarc?  That\'s silly.',
            created=(post_created_ds + datetime.timedelta(hours=1)))
        post1.save()

        self.refresh()

        # The thread/post should not show up in results for items
        # created AFTER 1/12/2010.
        response = self.client.get(reverse('search'), {
            'author': '', 'created': '2', 'created_date': '01/12/2010',
            'updated': '0', 'updated_date': '', 'sortby': '0',
            'a': '1', 'w': '4', 'q': 'hsarc',
            'format': 'json'
        })

        eq_(200, response.status_code)

        content = json.loads(response.content)
        eq_(content['total'], 0)

        # The thread/post should show up in results for items created
        # AFTER 1/1/2010.
        response = self.client.get(reverse('search'), {
            'author': '', 'created': '2', 'created_date': '01/01/2010',
            'updated': '0', 'updated_date': '', 'sortby': '0',
            'a': '1', 'w': '4', 'q': 'hsarc',
            'format': 'json'
        })

        eq_(200, response.status_code)

        content = json.loads(response.content)
        eq_(content['total'], 1)

        # The thread/post should show up in results for items created
        # BEFORE 1/12/2010.
        response = self.client.get(reverse('search'), {
            'author': '', 'created': '1', 'created_date': '01/12/2010',
            'updated': '0', 'updated_date': '', 'sortby': '0',
            'a': '1', 'w': '4', 'q': 'hsarc',
            'format': 'json'
        })

        eq_(200, response.status_code)

        content = json.loads(response.content)
        eq_(content['total'], 1)

        # The thread/post should NOT show up in results for items
        # created BEFORE 12/31/2009.
        response = self.client.get(reverse('search'), {
            'author': '', 'created': '1', 'created_date': '12/31/2009',
            'updated': '0', 'updated_date': '', 'sortby': '0',
            'a': '1', 'w': '4', 'q': 'hsarc',
            'format': 'json'
        })

        eq_(200, response.status_code)

        content = json.loads(response.content)
        eq_(content['total'], 0)


class ElasticSearchUtilsTests(ElasticTestCase):
    def test_get_documents(self):
        q = question(save=True)
        self.refresh()
        docs = es_utils.get_documents(Question, [q.id])
        docs = [int(mem[u'id']) for mem in docs]
        eq_(docs, [q.id])
