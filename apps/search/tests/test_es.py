import json
import datetime

import mock
from django.conf import settings
from django.contrib.sites.models import Site
from django.http import QueryDict
from django.utils.http import urlquote
from elasticutils import get_es
from nose import SkipTest
from nose.tools import eq_
from pyquery import PyQuery as pq
from test_utils import TestCase

from forums.tests import forum, thread, post
from questions.tests import question, answer, answervote, questionvote
from questions.models import Question
import search as constants
from search import es_utils
from search.models import generate_tasks
from sumo.tests import LocalizingClient
from sumo.urlresolvers import reverse
from users.tests import user
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
        super(ElasticTestCase, cls).tearDownClass()
        if not cls.skipme:
            # Restore old settings.
            es_utils.READ_INDEX = cls._old_read_index
            es_utils.WRITE_INDEX = cls._old_write_index

    def setUp(self):
        if self.skipme:
            raise SkipTest

        super(ElasticTestCase, self).setUp()
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

    def test_search_metrics(self):
        """Ensure that query strings are added to search results"""
        # Need at least one search result to get links.
        d1 = document(title=u'audio audio', locale=u'en-US', category=10,
                      save=True)
        d1.tags.add(u'desktop')
        revision(document=d1, is_approved=True, save=True)

        self.refresh()

        response = self.client.get(reverse('search'), {
            'q': 'audio', 'tags': 'desktop', 'w': '1', 'a': '1'
        })
        eq_(200, response.status_code)

        doc = pq(response.content)
        _, _, qs = doc('a.title:first').attr('href').partition('?')
        q = QueryDict(qs)
        eq_('audio', q['s'])
        eq_('s', q['as'])
        eq_('0', q['r'])

    def test_front_page_search_paging(self):
        """Tests the weird bucketing we do for front page searches

        Currently, the paging is set to 20, so for the first page of
        results for a front page search, you get 10 kb documents and
        then 10 question results.

        """
        # Create 30 documents
        for i in range(30):
            doc = document(title=u'How to fix your audio %d' % i,
                           locale=u'en-US', category=10, save=True)
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
        ques = question(title=u'audio fails', save=True)
        ques.tags.add(u'desktop')
        ans = answer(content=u'volume', question=ques, save=True)
        answervote(answer=ans, helpful=True, save=True)

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
        doc = document(title=u'audio', locale=u'en-US', category=10,
                       save=True)
        doc.tags.add(u'desktop')
        revision(document=doc, is_approved=True, save=True)

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
        doc = document(title=u'audio', locale=u'en-US', category=10, save=True)
        doc.tags.add(u'desktop')
        revision(document=doc, is_approved=True, save=True)

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

    def test_num_votes_none(self):
        """Tests num_voted filtering where num_votes is ''"""
        q = question(save=True)
        questionvote(question=q, save=True)

        self.refresh()

        qs = {'q': '', 'w': 2, 'a': 1, 'num_voted': 2, 'num_votes': ''}
        response = self.client.get(reverse('search'), qs)
        eq_(200, response.status_code)

    def test_forums_search(self):
        """This tests whether forum posts show up in searches"""
        thread1 = thread(title=u'crash', save=True)
        post(thread=thread1, content=u'hsarc?', save=True)

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
        """Tests created/created_date filtering for forums"""
        post_created_ds = datetime.datetime(2010, 1, 1, 12, 00)
        thread1 = thread(title=u'crash', created=post_created_ds, save=True)
        post(thread=thread1,
             created=(post_created_ds + datetime.timedelta(hours=1)),
             save=True)

        self.refresh()

        # The thread/post should not show up in results for items
        # created AFTER 1/12/2010.
        response = self.client.get(reverse('search'), {
            'author': '', 'created': '2', 'created_date': '01/12/2010',
            'updated': '0', 'updated_date': '', 'sortby': '0',
            'a': '1', 'w': '4', 'q': 'crash',
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
            'a': '1', 'w': '4', 'q': 'crash',
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
            'a': '1', 'w': '4', 'q': 'crash',
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
            'a': '1', 'w': '4', 'q': 'crash',
            'format': 'json'
        })

        eq_(200, response.status_code)

        content = json.loads(response.content)
        eq_(content['total'], 0)

    def test_multi_word_tag_search(self):
        """Tests searching for tags with spaces in them"""
        ques = question(title=u'audio', save=True)
        ques.tags.add(u'Windows 7')

        self.refresh()

        response = self.client.get(reverse('search'), {
            'q': 'audio', 'q_tags': 'Windows 7', 'w': '2', 'a': '1',
            'sortby': '0', 'format': 'json'
        })

        eq_(200, response.status_code)

        content = json.loads(response.content)
        eq_(content['total'], 1)


class ElasticSearchUnifiedViewTests(ElasticTestCase):
    client_class = LocalizingClient

    def setUp(self):
        super(ElasticSearchUnifiedViewTests, self).setUp()
        Flag.objects.create(name='esunified', everyone=True)

    def test_meta_tags(self):
        """Tests that the search results page  has the right meta tags"""
        url_ = reverse('search')
        response = self.client.get(url_, {'q': 'contribute'})

        doc = pq(response.content)
        metas = doc('meta')
        eq_(3, len(metas))

    def test_search_cookie(self):
        """Set a cookie with the latest search term."""
        data = {'q': u'pagap\xf3 banco'}
        cookie = settings.LAST_SEARCH_COOKIE
        response = self.client.get(reverse('search', locale='fr'), data)
        assert cookie in response.cookies
        eq_(urlquote(data['q']), response.cookies[cookie].value)

    def test_front_page_search_for_questions(self):
        """This tests whether doing a search from the front page returns
        question results.

        Bug #709202.

        """
        # Create a question with an answer with an answervote that
        # marks the answer as helpful.  The question should have the
        # "desktop" tag.
        ques = question(title=u'audio', save=True)
        ques.tags.add(u'desktop')
        ans = answer(question=ques, content=u'volume', save=True)
        answervote(answer=ans, helpful=True, save=True)

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
        doc = document(title=u'audio', locale=u'en-US', category=10, save=True)
        doc.tags.add(u'desktop')
        revision(document=doc, is_approved=True, save=True)

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

    def test_front_page_only_shows_wiki_and_questions(self):
        """Tests that the front page doesn't show forums

        This verifies that we're only showing documents of the type
        that should be shown and that the filters on model are working
        correctly.

        Bug #767394

        """
        ques = question(title=u'audio', save=True)
        ques.tags.add(u'desktop')
        ans = answer(question=ques, content=u'volume', save=True)
        answervote(answer=ans, helpful=True, save=True)

        doc = document(title=u'audio', locale=u'en-US', category=10, save=True)
        doc.tags.add(u'desktop')
        revision(document=doc, is_approved=True, save=True)

        thread1 = thread(title=u'audio', save=True)
        post(thread=thread1, save=True)

        self.refresh()

        response = self.client.get(reverse('search'), {
            'q_tags': 'desktop', 'product': 'desktop', 'q': 'audio',
            'format': 'json'
        })

        eq_(200, response.status_code)

        content = json.loads(response.content)
        eq_(content['total'], 2)

    def test_advanced_search_for_wiki_no_query(self):
        """Tests advanced search with no query"""
        doc = document(locale=u'en-US', category=10, save=True)
        doc.tags.add(u'desktop')
        revision(document=doc, is_approved=True, save=True)

        self.refresh()

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
            'q': 'tags', 'tags': 'desktop', 'w': '2', 'a': '1', 'sortby': '3',
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

    def test_num_votes_none(self):
        """Tests num_voted filtering where num_votes is ''"""
        q = question(save=True)
        questionvote(question=q, save=True)

        self.refresh()

        qs = {'q': '', 'w': 2, 'a': 1, 'num_voted': 2, 'num_votes': ''}
        response = self.client.get(reverse('search'), qs)
        eq_(200, response.status_code)

    def test_forums_search(self):
        """This tests whether forum posts show up in searches"""
        thread1 = thread(title=u'crash', save=True)
        post(thread=thread1, save=True)

        self.refresh()

        response = self.client.get(reverse('search'), {
            'author': '', 'created': '0', 'created_date': '',
            'updated': '0', 'updated_date': '', 'sortby': '0',
            'a': '1', 'w': '4', 'q': 'crash',
            'format': 'json'
        })

        eq_(200, response.status_code)

        content = json.loads(response.content)
        eq_(content['total'], 1)

    def test_forums_thread_created(self):
        """Tests created/created_date filtering for forums"""
        post_created_ds = datetime.datetime(2010, 1, 1, 12, 00)
        thread1 = thread(title=u'crash', created=post_created_ds, save=True)
        post(thread=thread1,
             created=(post_created_ds + datetime.timedelta(hours=1)),
             save=True)

        self.refresh()

        # The thread/post should not show up in results for items
        # created AFTER 1/12/2010.
        response = self.client.get(reverse('search'), {
            'author': '', 'created': '2', 'created_date': '01/12/2010',
            'updated': '0', 'updated_date': '', 'sortby': '0',
            'a': '1', 'w': '4', 'q': 'crash',
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
            'a': '1', 'w': '4', 'q': 'crash',
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
            'a': '1', 'w': '4', 'q': 'crash',
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
            'a': '1', 'w': '4', 'q': 'crash',
            'format': 'json'
        })

        eq_(200, response.status_code)

        content = json.loads(response.content)
        eq_(content['total'], 0)

    def test_multi_word_tag_search(self):
        """Tests searching for tags with spaces in them"""
        ques = question(title=u'audio', save=True)
        ques.tags.add(u'Windows 7')

        self.refresh()

        response = self.client.get(reverse('search'), {
            'q': 'audio', 'q_tags': 'Windows 7', 'w': '2', 'a': '1',
            'sortby': '0', 'format': 'json'
        })

        eq_(200, response.status_code)

        content = json.loads(response.content)
        eq_(content['total'], 1)

    def test_category_invalid(self):
        """Tests passing an invalid category"""
        # wiki and questions
        ques = question(title=u'q1 audio', save=True)
        ques.tags.add(u'desktop')
        ans = answer(question=ques, save=True)
        answervote(answer=ans, helpful=True, save=True)

        d1 = document(title=u'd1 audio', locale=u'en-US', category=10,
                      is_archived=False, save=True)
        d1.tags.add(u'desktop')
        revision(document=d1, is_approved=True, save=True)

        self.refresh()

        qs = {'a': 1, 'w': 3, 'format': 'json', 'category': 'invalid'}
        response = self.client.get(reverse('search'), qs)
        eq_(2, json.loads(response.content)['total'])

    def test_created(self):
        """Basic functionality of created filter."""
        created_ds = datetime.datetime(2010, 6, 19, 12, 00)

        # on 6/19/2010
        q1 = question(title=u'q1 audio', created=created_ds, save=True)
        q1.tags.add(u'desktop')
        ans = answer(question=q1, save=True)
        answervote(answer=ans, helpful=True, save=True)

        # on 6/21/2010
        q2 = question(title=u'q2 audio',
                      created=(created_ds + datetime.timedelta(days=2)),
                      save=True)
        q2.tags.add(u'desktop')
        ans = answer(question=q2, save=True)
        answervote(answer=ans, helpful=True, save=True)

        self.refresh()

        qs = {'a': 1, 'w': 2, 'format': 'json',
              'sortby': 2, 'created_date': '06/20/2010'}

        qs['created'] = constants.INTERVAL_BEFORE
        response = self.client.get(reverse('search'), qs)
        results = json.loads(response.content)['results']
        eq_([q1.get_absolute_url()], [r['url'] for r in results])

        qs['created'] = constants.INTERVAL_AFTER
        response = self.client.get(reverse('search'), qs)
        results = json.loads(response.content)['results']
        eq_([q2.get_absolute_url()], [r['url'] for r in results])

    def test_sortby_invalid(self):
        """Invalid created_date is ignored."""
        qs = {'a': 1, 'w': 4, 'format': 'json', 'sortby': ''}
        response = self.client.get(reverse('search'), qs)
        eq_(200, response.status_code)

    def test_created_date_invalid(self):
        """Invalid created_date is ignored."""
        thread1 = thread(save=True)
        post(thread=thread1, save=True)

        self.refresh()

        qs = {'a': 1, 'w': 4, 'format': 'json',
              'created': constants.INTERVAL_AFTER,
              'created_date': 'invalid'}
        response = self.client.get(reverse('search'), qs)
        eq_(1, json.loads(response.content)['total'])

    def test_created_date_nonexistent(self):
        """created is set while created_date is left out of the query."""
        qs = {'a': 1, 'w': 2, 'format': 'json', 'created': 1}
        response = self.client.get(reverse('search'), qs)
        eq_(200, response.status_code)

    def test_updated_invalid(self):
        """Invalid updated_date is ignored."""
        thread1 = thread(save=True)
        post(thread=thread1, save=True)

        self.refresh()

        qs = {'a': 1, 'w': 4, 'format': 'json',
              'updated': 1, 'updated_date': 'invalid'}
        response = self.client.get(reverse('search'), qs)
        eq_(1, json.loads(response.content)['total'])

    def test_updated_nonexistent(self):
        """updated is set while updated_date is left out of the query."""
        thread1 = thread(save=True)
        post(thread=thread1, save=True)

        self.refresh()

        qs = {'a': 1, 'w': 2, 'format': 'json', 'updated': 1}
        response = self.client.get(reverse('search'), qs)
        eq_(response.status_code, 200)

    def test_asked_by(self):
        """Check several author values, including test for (anon)"""
        author_vals = (
            ('DoesNotExist', 0),
            ('jsocol', 2),
            ('pcraciunoiu', 2),
        )

        # Set up all the question data---creats users, creates the
        # questions, shove it all in the index, then query it and see
        # what happens.
        for name, number in author_vals:
            u = user(username=name, save=True)
            for i in range(number):
                ques = question(title=u'audio', creator=u, save=True)
                ques.tags.add(u'desktop')
                ans = answer(question=ques, save=True)
                answervote(answer=ans, helpful=True, save=True)

        self.refresh()

        qs = {'a': 1, 'w': 2, 'format': 'json'}

        for author, total in author_vals:
            qs.update({'asked_by': author})
            response = self.client.get(reverse('search'), qs)
            eq_(total, json.loads(response.content)['total'])

    def test_wiki_tags(self):
        """Search for tags, includes multiple."""
        for tags in ('extant', 'extant tagged'):
            doc = document(locale=u'en-US', category=10, save=True)
            for tag in tags.split(' '):
                doc.tags.add(tag)
            revision(document=doc, is_approved=True, save=True)

        self.refresh()

        qs = {'a': 1, 'w': 1, 'format': 'json'}
        tags_vals = (
            ('doesnotexist', 0),
            ('extant', 2),
            ('tagged', 1),
            ('extant tagged', 1),  # two tags
        )

        for tags, number in tags_vals:
            qs.update({'tags': tags})
            response = self.client.get(reverse('search'), qs)
            eq_(number, json.loads(response.content)['total'])

    def test_wiki_tags_inherit(self):
        """Translations inherit tags from their parents."""
        doc = document(locale=u'en-US', category=10, save=True)
        doc.tags.add(u'desktop')
        doc.tags.add(u'extant')
        revision(document=doc, is_approved=True, save=True)

        translated = document(locale=u'es', parent=doc, category=10,
                              save=True)
        revision(document=translated, is_approved=True, save=True)

        self.refresh()

        qs = {'a': 1, 'w': 1, 'format': 'json', 'tags': 'extant'}
        response = self.client.get(reverse('search', locale='es'), qs)
        eq_(1, json.loads(response.content)['total'])

    def test_products(self):
        """Search for products."""
        prod_vals = (
            ('mobile', 1),
            ('desktop', 1),
            ('sync', 2),
            ('FxHome', 0),
        )

        for prod, total in prod_vals:
            for i in range(total):
                doc = document(locale=u'en-US', category=10, save=True)
                doc.tags.add(prod)
                revision(document=doc, is_approved=True, save=True)

        self.refresh()

        qs = {'a': 1, 'w': 1, 'format': 'json'}

        for prod, total in prod_vals:
            qs.update({'product': prod})
            response = self.client.get(reverse('search'), qs)
            eq_(total, json.loads(response.content)['total'])

    def test_products_inherit(self):
        """Translations inherit products from their parents."""
        doc = document(locale=u'en-US', category=10, save=True)
        doc.tags.add(u'desktop')
        revision(document=doc, is_approved=True, save=True)

        translated = document(locale=u'fr', parent=doc, category=10,
                              save=True)
        revision(document=translated, is_approved=True, save=True)

        self.refresh()

        qs = {'a': 1, 'w': 1, 'format': 'json', 'product': 'desktop'}
        response = self.client.get(reverse('search', locale='fr'), qs)
        eq_(1, json.loads(response.content)['total'])

    def test_discussion_filter_author(self):
        """Filter by author in discussion forums."""
        author_vals = (
            ('DoesNotExist', 0),
            ('admin', 1),
            ('jsocol', 4),
        )

        for name, number in author_vals:
            u = user(username=name, save=True)
            for i in range(number):
                thread1 = thread(title=u'audio', save=True)
                post(thread=thread1, author=u, save=True)

        self.refresh()

        qs = {'a': 1, 'w': 4, 'format': 'json'}

        for author, total in author_vals:
            qs.update({'author': author})
            response = self.client.get(reverse('search'), qs)
            eq_(total, json.loads(response.content)['total'])

    def test_discussion_filter_sticky(self):
        """Filter for sticky threads."""
        thread1 = thread(title=u'audio', is_locked=True, is_sticky=True,
                         save=True)
        post(thread=thread1, save=True)

        self.refresh()

        qs = {'a': 1, 'w': 4, 'format': 'json', 'thread_type': 1, 'forum': 1}
        response = self.client.get(reverse('search'), qs)
        results = json.loads(response.content)['results']
        eq_(len(results), 1)

    def test_discussion_filter_locked(self):
        """Filter for locked threads."""
        thread1 = thread(title=u'audio', is_locked=True,
                         save=True)
        post(thread=thread1, save=True)

        self.refresh()

        qs = {'a': 1, 'w': 4, 'format': 'json', 'thread_type': 2}
        response = self.client.get(reverse('search'), qs)
        results = json.loads(response.content)['results']
        eq_(len(results), 1)

    def test_discussion_filter_sticky_locked(self):
        """Filter for locked and sticky threads."""
        thread1 = thread(title=u'audio', is_locked=True, is_sticky=True,
                         save=True)
        post(thread=thread1, save=True)

        self.refresh()

        qs = {'a': 1, 'w': 4, 'format': 'json', 'thread_type': (1, 2)}
        response = self.client.get(reverse('search'), qs)
        result = json.loads(response.content)['results'][0]
        eq_(thread1.get_absolute_url(), result['url'])

    def test_forums_filter_updated(self):
        """Filter for updated date."""
        post_updated_ds = datetime.datetime(2010, 5, 3, 12, 00)

        thread1 = thread(title=u't1 audio', save=True)
        post(thread=thread1, created=post_updated_ds, save=True)

        thread2 = thread(title=u't2 audio', save=True)
        post(thread=thread2,
             created=(post_updated_ds + datetime.timedelta(days=2)),
             save=True)

        self.refresh()

        qs = {'a': 1, 'w': 4, 'format': 'json',
              'sortby': 1, 'updated_date': '05/04/2010'}

        qs['updated'] = constants.INTERVAL_BEFORE
        response = self.client.get(reverse('search'), qs)
        results = json.loads(response.content)['results']
        eq_([thread1.get_absolute_url()], [r['url'] for r in results])

        qs['updated'] = constants.INTERVAL_AFTER
        response = self.client.get(reverse('search'), qs)
        results = json.loads(response.content)['results']
        eq_([thread2.get_absolute_url()], [r['url'] for r in results])

    def test_archived(self):
        """Ensure archived articles show only when requested."""
        doc = document(title=u'impalas', locale=u'en-US',
                 is_archived=True, save=True)
        revision(document=doc, summary=u'impalas',
                 is_approved=True, save=True)

        self.refresh()

        # include_archived gets the above document
        qs = {'q': 'impalas', 'a': 1, 'w': 1, 'format': 'json',
              'include_archived': 'on'}
        response = self.client.get(reverse('search'), qs)
        results = json.loads(response.content)['results']
        eq_(1, len(results))

        # no include_archived gets you nothing since the only
        # document in the index is archived
        qs = {'q': 'impalas', 'a': 0, 'w': 1, 'format': 'json'}
        response = self.client.get(reverse('search'), qs)
        results = json.loads(response.content)['results']
        eq_(0, len(results))

    def test_discussion_filter_forum(self):
        """Filter by forum in discussion forums."""
        forum1 = forum(name=u'Forum 1', save=True)
        thread1 = thread(forum=forum1, title=u'audio 1', save=True)
        post(thread=thread1, save=True)

        forum2 = forum(name=u'Forum 2', save=True)
        thread2 = thread(forum=forum2, title=u'audio 2', save=True)
        post(thread=thread2, save=True)

        import search.forms
        reload(search.forms)
        import search.views
        import search.forms
        search.views.SearchForm = search.forms.SearchForm

        # Wait... reload? WTF is that about? What's going on here is
        # that SearchForm pulls the list of forums from the db **at
        # module load time**. Since we need it to include the two
        # forums we just created, we need to reload the module and
        # rebind it in search.views. Otherwise when we go to get
        # cleaned_data from it, it ditches the forum data we so
        # lovingly put in our querystring and then our filters are
        # wrong and then this test FAILS.

        self.refresh()

        qs = {'a': 1, 'w': 4, 'format': 'json'}

        for forum_id in (forum1.id, forum2.id):
            qs['forum'] = int(forum_id)
            response = self.client.get(reverse('search'), qs)
            eq_(json.loads(response.content)['total'], 1)


class ElasticSearchUtilsTests(ElasticTestCase):
    def test_get_documents(self):
        q = question(save=True)
        self.refresh()
        docs = es_utils.get_documents(Question, [q.id])
        docs = [int(mem[u'id']) for mem in docs]
        eq_(docs, [q.id])


class ElasticSearchSuggestionsTests(ElasticTestCase):
    @mock.patch.object(Site.objects, 'get_current')
    def test_invalid_suggestions(self, get_current):
        """The suggestions API needs a query term."""
        get_current.return_value.domain = 'testserver'
        response = self.client.get(reverse('search.suggestions',
                                           locale='en-US'))
        eq_(400, response.status_code)
        assert not response.content

    @mock.patch.object(Site.objects, 'get_current')
    def test_suggestions(self, get_current):
        """Suggestions API is well-formatted."""
        get_current.return_value.domain = 'testserver'

        doc = document(title=u'doc1 audio', locale=u'en-US',
                 is_archived=False, save=True)
        revision(document=doc, summary=u'audio', content=u'audio',
                 is_approved=True, save=True)

        ques = question(title=u'q1 audio', save=True)
        ques.tags.add(u'desktop')
        ans = answer(question=ques, save=True)
        answervote(answer=ans, helpful=True, save=True)

        self.refresh()

        response = self.client.get(reverse('search.suggestions',
                                           locale='en-US'),
                                   {'q': 'audio'})
        eq_(200, response.status_code)
        eq_('application/x-suggestions+json', response['content-type'])
        results = json.loads(response.content)

        eq_('audio', results[0])
        eq_(2, len(results[1]))
        eq_(0, len(results[2]))
        eq_(2, len(results[3]))
