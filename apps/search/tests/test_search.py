"""
Tests for the search (sphinx) app.
"""
from functools import partial
import os
import shutil
import time
import json

from django.conf import settings
from django.contrib.sites.models import Site
from django.http import QueryDict
from django.utils.http import urlquote

import jingo
import mock
from nose import SkipTest
from nose.tools import eq_
from pyquery import PyQuery as pq

from forums.models import Thread, discussion_searcher
from questions.models import question_searcher
import search as constants
from search.tests import dummy_request
from search.utils import (start_sphinx, stop_sphinx, reindex,
                          clean_excerpt)
from sumo.tests import LocalizingClient, TestCase
from sumo.urlresolvers import reverse
from wiki.models import wiki_searcher


discussion_searcher = partial(discussion_searcher, dummy_request)
wiki_searcher = partial(wiki_searcher, dummy_request)
question_searcher = partial(question_searcher, dummy_request)


def render(s, context):
    t = jingo.env.from_string(s)
    return t.render(context)


class SphinxTestCase(TestCase):
    """
    This test case type can setUp and tearDown the sphinx daemon.  Use this
    when testing any feature that requires sphinx.
    """

    fixtures = ['users.json', 'search/documents.json',
                'posts.json', 'questions.json']

    @classmethod
    def setUpClass(cls):
        super(SphinxTestCase, cls).setUpClass()
        if not settings.SPHINX_SEARCHD or not settings.SPHINX_INDEXER:
            raise SkipTest()

        os.environ['DJANGO_ENVIRONMENT'] = 'test'

        if os.path.exists(settings.TEST_SPHINX_PATH):
            shutil.rmtree(settings.TEST_SPHINX_PATH)

        os.makedirs(os.path.join(settings.TEST_SPHINX_PATH, 'data'))
        os.makedirs(os.path.join(settings.TEST_SPHINX_PATH, 'log'))
        os.makedirs(os.path.join(settings.TEST_SPHINX_PATH, 'etc'))

        reindex()
        start_sphinx()
        time.sleep(1)

    @classmethod
    def tearDownClass(cls):
        stop_sphinx()
        super(SphinxTestCase, cls).tearDownClass()


# TODO(jsocol):
# * Add tests for all Questions filters.
# * Replace magic numbers with the defined constants.

class SearchTest(SphinxTestCase):
    client_class = LocalizingClient

    def test_indexer(self):
        results = wiki_searcher().query('audio')
        eq_(2, len(results))

    def test_content(self):
        """Ensure template is rendered with no errors for a common search"""
        response = self.client.get(reverse('search'), {'q': 'audio', 'w': 3})
        eq_('text/html; charset=utf-8', response['Content-Type'])
        eq_(200, response.status_code)

    def test_content_mobile(self):
        """Ensure mobile template is rendered."""
        self.client.cookies[settings.MOBILE_COOKIE] = 'on'
        response = self.client.get(reverse('search'), {'q': 'audio', 'w': 3})
        eq_('text/html; charset=utf-8', response['Content-Type'])
        eq_(200, response.status_code)

    def test_search_type_param(self):
        """Ensure that invalid values for search type (a=)
        does not cause errors"""
        response = self.client.get(reverse('search'), {'a': 'dontdie'})
        eq_('text/html; charset=utf-8', response['Content-Type'])
        eq_(200, response.status_code)

    def test_headers(self):
        """Verify caching headers of search forms and search results"""
        response = self.client.get(reverse('search'), {'q': 'audio', 'w': 3})
        eq_('max-age=%s' % (settings.SEARCH_CACHE_PERIOD * 60),
            response['Cache-Control'])
        assert 'Expires' in response
        response = self.client.get(reverse('search'))
        eq_('max-age=%s' % (settings.SEARCH_CACHE_PERIOD * 60),
            response['Cache-Control'])
        assert 'Expires' in response

    def test_page_invalid(self):
        """Ensure non-integer param doesn't throw exception."""
        qs = {'a': 1, 'format': 'json', 'page': 'invalid'}
        response = self.client.get(reverse('search'), qs)
        eq_(200, response.status_code)
        eq_(6, json.loads(response.content)['total'])

    def test_search_metrics(self):
        """Ensure that query strings are added to search results"""
        response = self.client.get(reverse('search'), {'q': 'audio', 'w': 3})
        doc = pq(response.content)
        _, _, qs = doc('a.title:first').attr('href').partition('?')
        q = QueryDict(qs)
        eq_('audio', q['s'])
        eq_('s', q['as'])
        eq_('0', q['r'])
        eq_('sph', q['e'])

    def test_category(self):
        results = wiki_searcher().filter(category__in=[10])
        eq_(5, len(results))
        results = wiki_searcher().filter(category__in=[30])
        eq_(1, len(results))

    def test_category_invalid(self):
        qs = {'a': 1, 'w': 3, 'format': 'json', 'category': 'invalid'}
        response = self.client.get(reverse('search'), qs)
        eq_(6, json.loads(response.content)['total'])

    def test_no_filter(self):
        """Test searching with no filters."""
        # Note: We keep the query('') here to force a new S and thus
        # not inadvertently test with an S that's not in an original
        # state.
        results = list(wiki_searcher().query(''))
        eq_(6, len(results))

    def test_range_filter(self):
        """Test filtering on a range."""
        results = wiki_searcher().filter(updated__gte=1284664176,
                                         updated__lte=1285765791)
        eq_(2, len(results))

    def test_sort_mode(self):
        """Test set_sort_mode()."""
        # Initialize client and attrs.
        test_for = ('updated', 'created', 'answers')

        i = 0
        for sort_mode in constants.SORT_QUESTIONS[1:]:  # Skip default sorting.
            results = list(question_searcher().order_by(*sort_mode)
                                              .values_dict(test_for[i]))
            eq_(4, len(results))

            # Compare first and second.
            x = results[0][test_for[i]]
            y = results[1][test_for[i]]
            assert x > y, '%s !> %s' % (x, y)
            i += 1

    def test_num_voted_none(self):
        qs = {'q': '', 'w': 2, 'a': 1, 'num_voted': 2, 'num_votes': ''}
        response = self.client.get(reverse('search'), qs)
        eq_(200, response.status_code)

    def test_created(self):
        """Basic functionality of created filter."""

        qs = {'a': 1, 'w': 2, 'format': 'json',
              'sortby': 2, 'created_date': '06/20/2010'}
        created_vals = (
            (1, '/3'),
            (2, '/1'),
        )

        for created, url_id in created_vals:
            qs.update({'created': created})
            response = self.client.get(reverse('search'), qs)
            result = json.loads(response.content)['results'][-1]
            url_end = result['url'].endswith(url_id)
            assert url_end, ('Url was "%s", expected to end with "%s"' %
                             (result['url'], url_id))

    def test_sortby_invalid(self):
        """Invalid created_date is ignored."""
        qs = {'a': 1, 'w': 4, 'format': 'json', 'sortby': ''}
        response = self.client.get(reverse('search'), qs)
        eq_(200, response.status_code)

    def test_created_invalid(self):
        """Invalid created_date is ignored."""
        qs = {'a': 1, 'w': 4, 'format': 'json',
              'created': 1, 'created_date': 'invalid'}
        response = self.client.get(reverse('search'), qs)
        eq_(5, json.loads(response.content)['total'])

    def test_created_nonexistent(self):
        """created is set while created_date is left out of the query."""
        qs = {'a': 1, 'w': 2, 'format': 'json', 'created': 1}
        response = self.client.get(reverse('search'), qs)
        eq_(200, response.status_code)

    def test_created_range_sanity(self):
        """Ensure that the created_date range is sane."""
        qs = {'a': 1, 'w': '2', 'q': 'contribute', 'created': '2',
              'format': 'json'}
        date_vals = ('05/28/2099', '05/28/1900', '05/28/1920')
        for date_ in date_vals:
            qs.update({'created_date': date_})
            response = self.client.get(reverse('search'), qs)
            eq_(0, json.loads(response.content)['total'])

    def test_updated(self):
        """Basic functionality of updated filter."""
        qs = {'a': 1, 'w': 2, 'format': 'json',
              'sortby': 1, 'updated_date': '06/20/2010'}
        updated_vals = (
            (1, '/4'),
            (2, '/2'),
        )

        for updated, url_id in updated_vals:
            qs.update({'updated': updated})
            response = self.client.get(reverse('search'), qs)
            result = json.loads(response.content)['results'][0]
            url_end = result['url'].endswith(url_id)
            assert url_end, ('Url was "%s", expected to end with "%s"' %
                             (result['url'], url_id))

    def test_updated_invalid(self):
        """Invalid updated_date is ignored."""
        qs = {'a': 1, 'w': 2, 'format': 'json',
              'updated': 1, 'updated_date': 'invalid'}
        response = self.client.get(reverse('search'), qs)
        eq_(4, json.loads(response.content)['total'])

    def test_updated_nonexistent(self):
        """updated is set while updated_date is left out of the query."""
        qs = {'a': 1, 'w': 2, 'format': 'json', 'updated': 1}
        response = self.client.get(reverse('search'), qs)
        eq_(response.status_code, 200)

    def test_updated_range_sanity(self):
        """Ensure that the updated_date range is sane."""
        qs = {'a': 1, 'w': '2', 'q': 'contribute', 'updated': '2',
              'format': 'json'}
        date_vals = ('05/28/2099', '05/28/1900', '05/28/1920')
        for date_ in date_vals:
            qs.update({'updated_date': date_})
            response = self.client.get(reverse('search'), qs)
            eq_(0, json.loads(response.content)['total'])

    def test_asked_by(self):
        """Check several author values, including test for (anon)"""
        qs = {'a': 1, 'w': 2, 'format': 'json'}
        author_vals = (
            ('DoesNotExist', 0),
            ('jsocol', 2),
            ('pcraciunoiu', 2),
        )

        for author, total in author_vals:
            qs.update({'asked_by': author})
            response = self.client.get(reverse('search'), qs)
            eq_(total, json.loads(response.content)['total'])

    def test_tags(self):
        """Search for tags, includes multiple."""
        qs = {'a': 1, 'w': 1, 'format': 'json'}
        tags_vals = (
            ('doesnotexist', 0),
            ('extant', 2),
            ('tagged', 1),
            ('extant tagged', 1),
        )

        for tag_string, total in tags_vals:
            qs.update({'tags': tag_string})
            response = self.client.get(reverse('search'), qs)
            eq_(total, json.loads(response.content)['total'])

    def test_tags_inherit(self):
        """Translations inherit tags from their parents."""
        qs = {'a': 1, 'w': 1, 'format': 'json', 'tags': 'extant'}
        response = self.client.get(reverse('search', locale='es'), qs)
        eq_(1, json.loads(response.content)['total'])

    def test_products(self):
        """Search for products."""
        qs = {'a': 1, 'w': 1, 'format': 'json'}
        prod_vals = (
            ('mobile', 1),
            ('desktop', 1),
            ('sync', 2),
            ('FxHome', 0),
        )

        for prod, total in prod_vals:
            qs.update({'product': prod})
            response = self.client.get(reverse('search'), qs)
            eq_(total, json.loads(response.content)['total'])

    def test_products_inherit(self):
        """Translations inherit products from their parents."""
        qs = {'a': 1, 'w': 1, 'format': 'json', 'product': 'desktop'}
        response = self.client.get(reverse('search', locale='fr'), qs)
        eq_(1, json.loads(response.content)['total'])

    def test_unicode_excerpt(self):
        """Unicode characters in the excerpt should not be a problem."""
        ws = (wiki_searcher().highlight('html')
                             .query(u'\u30c1')
                             .values_dict('html'))
        results = list(ws)
        try:
            excerpt = ws.excerpt(results[0])
            render('{{ c }}', {'c': excerpt})
        except UnicodeDecodeError:
            self.fail('Raised UnicodeDecodeError.')

    def test_utf8_excerpt(self):
        """Characters should stay in UTF-8."""
        q = u'fa\xe7on'
        ws = (wiki_searcher().highlight('html')
                             .query(u'fa\xe7on')
                             .values_dict('html'))

        results = list(ws)
        # page = Document.objects.get(pk=4)
        excerpt = clean_excerpt(ws.excerpt(results[0])[0][0])
        assert q in excerpt, u'%s not in %s' % (q, excerpt)

    def test_clean_excerpt(self):
        """clean_excerpt() should not allow disallowed HTML through."""
        in_ = '<b>test</b> <div>the start of something</div>'
        out_ = '<b>test</b> &lt;div&gt;the start of something&lt;/div&gt;'
        eq_(out_, clean_excerpt(in_))

    def test_meta_tags(self):
        url_ = reverse('search')
        response = self.client.get(url_, {'q': 'contribute'})

        doc = pq(response.content)
        metas = doc('meta')
        eq_(3, len(metas))

    def test_discussion_sanity(self):
        """Sanity check for discussion forums search client."""
        dis_s = (discussion_searcher()
                     .highlight('content')
                     .filter(author_ord='admin')
                     .query('post').values_dict('id', 'content'))
        results = list(dis_s)
        eq_(1, len(results))
        eq_([u'yet another <b>post</b>'], dis_s.excerpt(results[0])[0])

    def test_discussion_filter_author(self):
        """Filter by author in discussion forums."""
        qs = {'a': 1, 'w': 4, 'format': 'json'}
        author_vals = (
            ('DoesNotExist', 0),
            ('admin', 1),
            ('jsocol', 4),
        )

        for author, total in author_vals:
            qs.update({'author': author})
            response = self.client.get(reverse('search'), qs)
            eq_(total, json.loads(response.content)['total'])

    def test_discussion_filter_forum(self):
        """Filter by forum in discussion forums."""
        raise SkipTest  # TODO: Figure out why this randomly started failing.
        qs = {'a': 1, 'w': 4, 'format': 'json'}
        forum_vals = (
            # (forum_id, num_results)
            (1, 4),
            (2, 1),
            (3, 0),  # this forum does not exist
        )

        for forum_id, total in forum_vals:
            qs.update({'forum': forum_id})
            response = self.client.get(reverse('search'), qs)
            eq_(total, json.loads(response.content)['total'])

    def test_discussion_filter_sticky(self):
        """Filter for sticky threads."""
        raise SkipTest  # TODO: Figure out why this randomly started failing.
        qs = {'a': 1, 'w': 4, 'format': 'json', 'thread_type': 1, 'forum': 1}
        response = self.client.get(reverse('search'), qs)
        result = json.loads(response.content)['results'][0]
        eq_(u'Sticky Thread', result['title'])

    def test_discussion_filter_locked(self):
        """Filter for locked threads."""
        raise SkipTest  # TODO: Figure out why this randomly started failing.
        qs = {'a': 1, 'w': 4, 'format': 'json', 'thread_type': 2,
              'forum': 1, 'q': 'locked'}
        response = self.client.get(reverse('search'), qs)
        result = json.loads(response.content)['results'][0]
        eq_(u'Locked Thread', result['title'])

    def test_discussion_filter_sticky_locked(self):
        """Filter for locked and sticky threads."""
        qs = {'a': 1, 'w': 4, 'format': 'json', 'thread_type': (1, 2)}
        response = self.client.get(reverse('search'), qs)
        result = json.loads(response.content)['results'][0]
        eq_(u'Locked Sticky Thread', result['title'])

    def test_discussion_filter_created(self):
        """Filter for created date."""
        qs = {'a': 1, 'w': 4, 'format': 'json',
              'sortby': 2, 'created_date': '05/03/2010'}
        created_vals = (
            (1, '/1'),
            (2, '/5'),
        )

        for created, url_id in created_vals:
            qs.update({'created': created})
            response = self.client.get(reverse('search'), qs)
            result = json.loads(response.content)['results'][-1]
            url_end = result['url'].endswith(url_id)
            assert url_end, ('Url was "%s", expected to end with "%s"' %
                             (result['url'], url_id))

    def test_discussion_filter_updated(self):
        """Filter for updated date."""
        qs = {'a': 1, 'w': 4, 'format': 'json',
              'sortby': 1, 'updated_date': '05/04/2010'}
        updated_vals = (
            (1, '/1'),
            (2, '/4'),
        )

        for updated, url_id in updated_vals:
            qs.update({'updated': updated})
            response = self.client.get(reverse('search'), qs)
            result = json.loads(response.content)['results'][0]
            url_end = result['url'].endswith(url_id)
            assert url_end, ('URL was "%s", expected to end with "%s"' %
                             (result['url'], url_id))

    def test_discussion_sort_mode(self):
        """Test set groupsort."""
        # Initialize client and attrs.
        ds = discussion_searcher()
        test_for = ('updated', 'created')

        i = 0
        # This tests -updated and -created and skips the default
        # sorting and -replies.
        for groupsort in constants.GROUPSORT[1:-1]:
            results = list(ds.group_by('thread_id', groupsort))
            eq_(5, len(results))

            # Compare first and last.
            assert (getattr(results[0], test_for[i]) >
                    getattr(results[-1], test_for[i]))
            i += 1

        # We have to do -replies group sort separate because replies
        # is an attribute of Thread and not Post.
        results = list(ds.group_by('thread_id', '-replies'))
        eq_(5, len(results))
        t0 = Thread.objects.get(pk=results[0].thread_id)
        tn1 = Thread.objects.get(pk=results[-1].thread_id)
        assert (t0.replies > tn1.replies)

    def test_wiki_index_keywords(self):
        """The keywords field of a revision is indexed."""
        results = list(wiki_searcher().query('foobar'))
        eq_(1, len(results))
        eq_(3, results[0].id)

    def test_wiki_index_summary(self):
        """The summary field of a revision is indexed."""
        results = list(wiki_searcher().query('whatever'))
        eq_(1, len(results))
        eq_(3, results[0].id)

    def test_wiki_index_content(self):
        """Obviously the content should be indexed."""
        results = list(wiki_searcher().query('video'))
        eq_(1, len(results))
        eq_(1, results[0].id)

    def test_wiki_index_strip_html(self):
        """HTML should be stripped, not indexed."""
        results = list(wiki_searcher().query('strong'))
        eq_(0, len(results))

    def test_ngram_chars(self):
        """Ideographs are handled correctly."""
        results = list(wiki_searcher().query(u'\u30c1'))
        eq_(1, len(results))
        eq_(2, results[0].id)

    def test_no_syntax_error(self):
        """Test that special chars cannot cause a syntax error."""
        results = list(wiki_searcher().query('video^$'))
        eq_(1, len(results))

        results = list(wiki_searcher().query('video^^^$$$^'))
        eq_(1, len(results))

        results = list(wiki_searcher().query('google.com/ig'))
        eq_(0, len(results))

    def test_clean_hyphens(self):
        """Hyphens in words aren't special characters."""
        results = list(wiki_searcher().query('marque-page'))
        eq_(1, len(results))

    def test_exclude_words(self):
        """Excluding words with -word works."""
        results = list(wiki_searcher().query('spanish'))
        eq_(1, len(results))

        results = list(wiki_searcher().query('spanish -content'))
        eq_(0, len(results))

    def test_no_redirects(self):
        """Redirect articles should never appear in search results."""
        results = list(wiki_searcher().query('ghosts'))
        eq_(1, len(results))

    def test_search_cookie(self):
        """Set a cookie with the latest search term."""
        data = {'q': u'pagap\xf3 banco'}
        cookie = settings.LAST_SEARCH_COOKIE
        response = self.client.get(reverse('search', locale='fr'), data)
        assert cookie in response.cookies
        eq_(urlquote(data['q']), response.cookies[cookie].value)

    @mock.patch.object(Site.objects, 'get_current')
    def test_suggestions(self, get_current):
        """Suggestions API is well-formatted."""
        get_current.return_value.domain = 'testserver'

        response = self.client.get(reverse('search.suggestions',
                                           locale='en-US'),
                                   {'q': 'audio'})
        eq_(200, response.status_code)
        eq_('application/x-suggestions+json', response['content-type'])
        results = json.loads(response.content)
        eq_('audio', results[0])
        eq_(3, len(results[1]))
        eq_(0, len(results[2]))
        eq_(3, len(results[3]))

    @mock.patch.object(Site.objects, 'get_current')
    def test_invalid_suggestions(self, get_current):
        """The suggestions API needs a query term."""
        get_current.return_value.domain = 'testserver'
        response = self.client.get(reverse('search.suggestions',
                                           locale='en-US'))
        eq_(400, response.status_code)
        assert not response.content

    def test_archived(self):
        """Ensure archived articles show only when requested."""
        qs = {'q': 'impalas', 'a': 1, 'w': 1, 'format': 'json',
              'include_archived': 'on'}
        response = self.client.get(reverse('search'), qs)
        results = json.loads(response.content)['results']
        eq_(1, len(results))
        assert results[0]['url'].endswith('archived-article')

        qs = {'q': 'impalas', 'a': 0, 'w': 1, 'format': 'json'}
        response = self.client.get(reverse('search'), qs)
        results = json.loads(response.content)['results']
        eq_([], results)
