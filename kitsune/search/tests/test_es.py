# -*- coding: utf-8 -*-
import json
import unittest
from datetime import datetime, timedelta

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.contrib.sites.models import Site
from django.http import QueryDict
from django.utils.http import urlquote

import mock
from nose.tools import eq_
from pyquery import PyQuery as pq

from kitsune import search as constants
from kitsune.access.tests import permission
from kitsune.forums.tests import forum, post, restricted_forum, thread
from kitsune.products.tests import product, topic
from kitsune.questions.models import QuestionMappingType
from kitsune.questions.tests import question, answer, answervote, questionvote
from kitsune.search import es_utils
from kitsune.search.models import generate_tasks
from kitsune.search.tests import ElasticTestCase
from kitsune.sumo.tests import LocalizingClient
from kitsune.sumo.urlresolvers import reverse
from kitsune.users.tests import group, user
from kitsune.wiki.models import DocumentMappingType
from kitsune.wiki.tests import document, revision, helpful_vote


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


class ElasticSearchUnifiedViewTests(ElasticTestCase):
    client_class = LocalizingClient

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

    def test_empty_pages(self):
        """Tests requesting a page that has no results"""
        ques = question(title=u'audio', save=True)
        ques.tags.add(u'desktop')
        ans = answer(question=ques, content=u'volume', save=True)
        answervote(answer=ans, helpful=True, save=True)

        self.refresh()

        qs = {'q': 'audio', 'page': 81}
        response = self.client.get(reverse('search'), qs)
        eq_(200, response.status_code)

    def test_default_search_for_questions(self):
        """This tests whether doing a default search returns
        question results.

        Bug #709202.

        """
        # Create a question with an answer with an answervote that
        # marks the answer as helpful.  The question should have the
        # "desktop" tag.
        p = product(title=u'firefox', slug=u'desktop', save=True)
        ques = question(title=u'audio', save=True)
        ques.products.add(p)
        ans = answer(question=ques, content=u'volume', save=True)
        answervote(answer=ans, helpful=True, save=True)

        self.refresh()

        # This is the search that you get when you start on the sumo
        # homepage and do a search from the box with two differences:
        # first, we do it in json since it's easier to deal with
        # testing-wise and second, we search for 'audio' since we have
        # data for that.
        response = self.client.get(reverse('search'), {
            'q': 'audio', 'format': 'json'})

        eq_(200, response.status_code)

        content = json.loads(response.content)
        eq_(content['total'], 1)

        # This is another search that picks up results based on the
        # answer_content.  answer_content is in a string array, so
        # this makes sure that works.
        response = self.client.get(reverse('search'), {
            'q': 'volume', 'format': 'json'})

        eq_(200, response.status_code)

        content = json.loads(response.content)
        eq_(content['total'], 1)

    def test_default_search_for_wiki(self):
        """This tests whether doing a default search returns wiki document
        results.

        Bug #709202.

        """
        doc = document(title=u'audio', locale=u'en-US', category=10, save=True)
        doc.products.add(product(title=u'firefox', slug=u'desktop', save=True))
        revision(document=doc, is_approved=True, save=True)

        self.refresh()

        # This is the search that you get when you start on the sumo
        # homepage and do a search from the box with two differences:
        # first, we do it in json since it's easier to deal with
        # testing-wise and second, we search for 'audio' since we have
        # data for that.
        response = self.client.get(reverse('search'), {
            'q': 'audio', 'format': 'json'})

        eq_(200, response.status_code)

        content = json.loads(response.content)
        eq_(content['total'], 1)

    def test_default_only_shows_wiki_and_questions(self):
        """Tests that the default search doesn't show forums

        This verifies that we're only showing documents of the type
        that should be shown and that the filters on model are working
        correctly.

        Bug #767394

        """
        p = product(slug=u'desktop', save=True)
        ques = question(title=u'audio', save=True)
        ques.products.add(p)
        ans = answer(question=ques, content=u'volume', save=True)
        answervote(answer=ans, helpful=True, save=True)

        doc = document(title=u'audio', locale=u'en-US', category=10, save=True)
        doc.products.add(p)
        revision(document=doc, is_approved=True, save=True)

        thread1 = thread(title=u'audio', save=True)
        post(thread=thread1, save=True)

        self.refresh()

        response = self.client.get(reverse('search'), {
            'q': 'audio', 'format': 'json'})

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

    def test_advanced_search_sortby_documents_helpful(self):
        """Tests advanced search with a sortby_documents by helpful"""
        r1 = revision(is_approved=True, save=True)
        r2 = revision(is_approved=True, save=True)
        helpful_vote(revision=r2, helpful=True, save=True)

        # Note: We have to wipe and rebuild the index because new
        # helpful_votes don't update the index data.
        self.setup_indexes()
        self.reindex_and_refresh()

        # r2.document should come first with 1 vote.
        response = self.client.get(reverse('search'), {
            'w': '1', 'a': '1', 'sortby_documents': 'helpful',
            'format': 'json'})
        eq_(200, response.status_code)

        content = json.loads(response.content)
        eq_(r2.document.title, content['results'][0]['title'])

        # Vote twice on r1, now it should come first.
        helpful_vote(revision=r1, helpful=True, save=True)
        helpful_vote(revision=r1, helpful=True, save=True)

        self.setup_indexes()
        self.reindex_and_refresh()

        response = self.client.get(reverse('search'), {
            'w': '1', 'a': '1', 'sortby_documents': 'helpful',
            'format': 'json'})
        eq_(200, response.status_code)

        content = json.loads(response.content)
        eq_(r1.document.title, content['results'][0]['title'])

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

    def test_forums_search_authorized_forums(self):
        """Only authorized people can search certain forums"""
        # Create two threads: one in a restricted forum and one not.
        forum1 = forum(name=u'ou812forum', save=True)
        thread1 = thread(forum=forum1, save=True)
        post(thread=thread1, content=u'audio', save=True)

        forum2 = restricted_forum(name=u'restrictedkeepout', save=True)
        thread2 = thread(forum=forum2, save=True)
        post(thread=thread2, content=u'audio restricted', save=True)

        self.refresh()

        # Do a search as an anonymous user but don't specify the
        # forums to filter on. Should only see one of the posts.
        response = self.client.get(reverse('search'), {
            'author': '',
            'created': '0',
            'created_date': '',
            'updated': '0',
            'updated_date': '',
            'sortby': '0',
            'a': '1',
            'w': '4',
            'q': 'audio',
            'format': 'json'
        })

        eq_(200, response.status_code)
        content = json.loads(response.content)
        eq_(content['total'], 1)

        # Do a search as an authorized user but don't specify the
        # forums to filter on. Should see both posts.
        u = user(save=True)
        g = group(save=True)
        g.user_set.add(u)
        ct = ContentType.objects.get_for_model(forum2)
        permission(codename='forums_forum.view_in_forum', content_type=ct,
                   object_id=forum2.id, group=g, save=True)

        self.client.login(username=u.username, password='testpass')
        response = self.client.get(reverse('search'), {
            'author': '',
            'created': '0',
            'created_date': '',
            'updated': '0',
            'updated_date': '',
            'sortby': '0',
            'a': '1',
            'w': '4',
            'q': 'audio',
            'format': 'json'
        })

        # Sees both results
        eq_(200, response.status_code)
        content = json.loads(response.content)
        eq_(content['total'], 2)

    def test_forums_search_authorized_forums_specifying_forums(self):
        """Only authorized people can search certain forums they specified"""
        # Create two threads: one in a restricted forum and one not.
        forum1 = forum(name=u'ou812forum', save=True)
        thread1 = thread(forum=forum1, save=True)
        post(thread=thread1, content=u'audio', save=True)

        forum2 = restricted_forum(name=u'restrictedkeepout', save=True)
        thread2 = thread(forum=forum2, save=True)
        post(thread=thread2, content=u'audio restricted', save=True)

        self.refresh()

        # Do a search as an anonymous user and specify both
        # forums. Should only see the post from the unrestricted
        # forum.
        response = self.client.get(reverse('search'), {
            'author': '',
            'created': '0',
            'created_date': '',
            'updated': '0',
            'updated_date': '',
            'sortby': '0',
            'forum': [forum1.id, forum2.id],
            'a': '1',
            'w': '4',
            'q': 'audio',
            'format': 'json'
        })

        eq_(200, response.status_code)
        content = json.loads(response.content)
        eq_(content['total'], 1)

        # Do a search as an authorized user and specify both
        # forums. Should see both posts.
        u = user(save=True)
        g = group(save=True)
        g.user_set.add(u)
        ct = ContentType.objects.get_for_model(forum2)
        permission(codename='forums_forum.view_in_forum', content_type=ct,
                   object_id=forum2.id, group=g, save=True)

        self.client.login(username=u.username, password='testpass')
        response = self.client.get(reverse('search'), {
            'author': '',
            'created': '0',
            'created_date': '',
            'updated': '0',
            'updated_date': '',
            'sortby': '0',
            'forum': [forum1.id, forum2.id],
            'a': '1',
            'w': '4',
            'q': 'audio',
            'format': 'json'
        })

        # Sees both results
        eq_(200, response.status_code)
        content = json.loads(response.content)
        eq_(content['total'], 2)

    def test_forums_thread_created(self):
        """Tests created/created_date filtering for forums"""
        post_created_ds = datetime(2010, 1, 1, 12, 00)
        thread1 = thread(title=u'crash', created=post_created_ds, save=True)
        post(thread=thread1,
             created=(post_created_ds + timedelta(hours=1)),
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
        created_ds = datetime(2010, 6, 19, 12, 00)

        # on 6/19/2010
        q1 = question(title=u'q1 audio', created=created_ds, save=True)
        q1.tags.add(u'desktop')
        ans = answer(question=q1, save=True)
        answervote(answer=ans, helpful=True, save=True)

        # on 6/21/2010
        q2 = question(title=u'q2 audio',
                      created=(created_ds + timedelta(days=2)),
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

    def test_created_default(self):
        """Questions older than 180 days aren't returned by default."""
        max_age_days = settings.SEARCH_DEFAULT_MAX_QUESTION_AGE / 60 / 60 / 24
        # Older than max_age_days:
        created = datetime.now() - timedelta(days=max_age_days + 1)
        q1 = question(title=u'q1 audio', created=created, save=True)
        q1.tags.add(u'desktop')
        ans = answer(question=q1, save=True)
        answervote(answer=ans, helpful=True, save=True)

        # Younger than max_age_days:
        created = datetime.now() - timedelta(days=max_age_days - 1)
        q2 = question(title=u'q2 audio', created=created, save=True)
        q2.tags.add(u'desktop')
        ans = answer(question=q2, save=True)
        answervote(answer=ans, helpful=True, save=True)

        self.refresh()

        qs = {'format': 'json', 'q': 'audio'}

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

    def test_question_topics(self):
        """Search questions for topics."""
        p = product(save=True)
        t1 = topic(slug='doesnotexist', product=p, save=True)
        t2 = topic(slug='cookies', product=p, save=True)
        t3 = topic(slug='sync', product=p, save=True)

        q = question(save=True)
        q.topics.add(t2)
        q = question(save=True)
        q.topics.add(t2)
        q.topics.add(t3)

        self.refresh()

        topic_vals = (
            (t1.slug, 0),
            (t2.slug, 2),
            (t3.slug, 1),
            ([t2.slug, t3.slug], 1),
        )

        qs = {'a': 1, 'w': 2, 'format': 'json'}
        for topics, number in topic_vals:
            qs.update({'topics': topics})
            response = self.client.get(reverse('search'), qs)
            eq_(number, json.loads(response.content)['total'])

    def test_wiki_topics(self):
        """Search wiki for topics, includes multiple."""
        t1 = topic(slug='doesnotexist', save=True)
        t2 = topic(slug='extant', save=True)
        t3 = topic(slug='tagged', save=True)

        doc = document(locale=u'en-US', category=10, save=True)
        doc.topics.add(t2)
        revision(document=doc, is_approved=True, save=True)

        doc = document(locale=u'en-US', category=10, save=True)
        doc.topics.add(t2)
        doc.topics.add(t3)
        revision(document=doc, is_approved=True, save=True)

        self.refresh()

        topic_vals = (
            (t1.slug, 0),
            (t2.slug, 2),
            (t3.slug, 1),
            ([t2.slug, t3.slug], 1),
        )

        qs = {'a': 1, 'w': 1, 'format': 'json'}
        for topics, number in topic_vals:
            qs.update({'topics': topics})
            response = self.client.get(reverse('search'), qs)
            eq_(number, json.loads(response.content)['total'])

    def test_wiki_topics_inherit(self):
        """Translations inherit topics from their parents."""
        doc = document(locale=u'en-US', category=10, save=True)
        doc.topics.add(topic(slug='extant', save=True))
        revision(document=doc, is_approved=True, save=True)

        translated = document(locale=u'es', parent=doc, category=10,
                              save=True)
        revision(document=translated, is_approved=True, save=True)

        self.refresh()

        qs = {'a': 1, 'w': 1, 'format': 'json', 'topics': 'extant'}
        response = self.client.get(reverse('search', locale='es'), qs)
        eq_(1, json.loads(response.content)['total'])

    def test_question_products(self):
        """Search questions for products."""
        p1 = product(slug='b2g', save=True)
        p2 = product(slug='mobile', save=True)
        p3 = product(slug='desktop', save=True)

        q = question(save=True)
        q.products.add(p2)
        q = question(save=True)
        q.products.add(p2)
        q.products.add(p3)

        self.refresh()

        product_vals = (
            (p1.slug, 0),
            (p2.slug, 2),
            (p3.slug, 1),
            ([p2.slug, p3.slug], 1),
        )

        qs = {'a': 1, 'w': 2, 'format': 'json'}
        for products, number in product_vals:
            qs.update({'product': products})
            response = self.client.get(reverse('search'), qs)
            eq_(number, json.loads(response.content)['total'])

    def test_wiki_products(self):
        """Search wiki for products."""

        prod_vals = (
            (product(slug='b2g', save=True), 0),
            (product(slug='mobile', save=True), 1),
            (product(slug='desktop', save=True), 2),
        )

        for prod, total in prod_vals:
            for i in range(total):
                doc = document(locale=u'en-US', category=10, save=True)
                doc.products.add(prod)
                revision(document=doc, is_approved=True, save=True)

        self.refresh()

        qs = {'a': 1, 'w': 1, 'format': 'json'}

        for prod, total in prod_vals:
            qs.update({'product': prod.slug})
            response = self.client.get(reverse('search'), qs)
            eq_(total, json.loads(response.content)['total'])

    def test_wiki_products_inherit(self):
        """Translations inherit products from their parents."""
        doc = document(locale=u'en-US', category=10, save=True)
        p = product(title=u'Firefox', slug=u'desktop', save=True)
        doc.products.add(p)
        revision(document=doc, is_approved=True, save=True)

        translated = document(locale=u'fr', parent=doc, category=10,
                              save=True)
        revision(document=translated, is_approved=True, save=True)

        self.refresh()

        qs = {'a': 1, 'w': 1, 'format': 'json', 'product': p.slug}
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
        post_updated_ds = datetime(2010, 5, 3, 12, 00)

        thread1 = thread(title=u't1 audio', save=True)
        post(thread=thread1, created=post_updated_ds, save=True)

        thread2 = thread(title=u't2 audio', save=True)
        post(thread=thread2,
             created=(post_updated_ds + timedelta(days=2)),
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

        self.refresh()

        qs = {'a': 1, 'w': 4, 'format': 'json'}

        for forum_id in (forum1.id, forum2.id):
            qs['forum'] = int(forum_id)
            response = self.client.get(reverse('search'), qs)
            eq_(json.loads(response.content)['total'], 1)


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


class TestUtils(ElasticTestCase):
    def test_get_documents(self):
        q = question(save=True)
        self.refresh()

        docs = es_utils.get_documents(QuestionMappingType, [q.id])
        eq_(docs[0]['id'], q.id)


class TestTasks(ElasticTestCase):
    @mock.patch.object(QuestionMappingType, 'index')
    def test_tasks(self, index_fun):
        """Tests to make sure tasks are added and run"""
        q = question()
        # Don't call self.refresh here since that calls generate_tasks().

        eq_(index_fun.call_count, 0)

        q.save()
        generate_tasks()

        eq_(index_fun.call_count, 1)

    @mock.patch.object(QuestionMappingType, 'index')
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


class TestMappings(unittest.TestCase):
    def test_mappings(self):
        # This is more of a linter than a test. If it passes, then
        # everything is fine. If it fails, then it means things are
        # not fine. Not fine? Yeah, it means that there are two fields
        # with the same name, but different types in the
        # mappings. That doesn't work in ES.

        # Doing it as a test seemed like a good idea since
        # it's likely to catch epic problems, but isn't in the runtime
        # code.

        merged_mapping = {}

        for cls_name, mapping in es_utils.get_all_mappings().items():
            mapping = mapping['properties']

            for key, val in mapping.items():
                if key not in merged_mapping:
                    merged_mapping[key] = (val, [cls_name])
                    continue

                # FIXME - We're comparing two dicts here. This might
                # not work for non-trivial dicts.
                if merged_mapping[key][0] != val:
                    raise es_utils.MappingMergeError(
                        '%s key different for %s and %s' %
                        (key, cls_name, merged_mapping[key][1]))

                merged_mapping[key][1].append(cls_name)

        # If we get here, then we're fine.


class TestAnalyzers(ElasticTestCase):

    def setUp(self):
        super(TestAnalyzers, self).setUp()

        self.locale_data = {
            'en-US': {
                'analyzer': 'snowball-english',
                'content': 'I have a cat.',
            },
            'es': {
                'analyzer': 'snowball-spanish',
                'content': 'Tieno un gato.',
            },
            'ar': {
                'analyzer': 'arabic',
                'content': u'لدي اثنين من القطط',
            },
            'my': {
                'analyzer': 'custom-burmese',
                'content': u'အနုပညာ',
            },
            'he': {
                'analyzer': 'standard',
                'content': u'גאולוגיה היא אחד',
            }
        }

        self.docs = {}
        for locale, data in self.locale_data.items():
            d = document(locale=locale, save=True)
            revision(document=d, content=data['content'], is_approved=True,
                     save=True)
            self.locale_data[locale]['doc'] = d

        self.refresh()

    def test_analyzer_choices(self):
        """Check that the indexer picked the right analyzer."""

        ids = [d.id for d in self.docs.values()]
        docs = es_utils.get_documents(DocumentMappingType, ids)
        for doc in docs:
            locale = doc['locale']
            eq_(doc['_analyzer'], self.locale_data[locale]['analyzer'])

    def test_query_analyzer_upgrader(self):
        analyzer = 'snowball-english'
        before = {
            'document_title__text': 'foo',
            'document_locale__text': 'bar',
            'document_title__text_phrase': 'baz',
            'document_locale__text_phrase': 'qux'
        }
        expected = {
            'document_title__text_analyzer': ('foo', analyzer),
            'document_locale__text': 'bar',
            'document_title__text_phrase_analyzer': ('baz', analyzer),
            'document_locale__text_phrase': 'qux',
        }
        actual = es_utils.es_query_with_analyzer(before, 'en-US')
        eq_(actual, expected)

    def _check_locale_tokenization(self, locale, expected_tokens, p_tag=True):
        """
        Check that a given locale's document was tokenized correctly.

        * `locale` - The locale to check.
        * `expected_tokens` - An iterable of the tokens that should be
            found. If any tokens from this list are missing, or if any
            tokens not in this list are found, the check will fail.
        * `p_tag` - Default True. If True, an extra token will be added
            to `expected_tokens`: "p".

            This is because our wiki parser wraps it's content in <p>
            tags and many analyzers will tokenize a string like
            '<p>Foo</p>' as ['p', 'foo'] (the HTML tag is included in
            the tokenization). So this will show up in the tokenization
            during this test. Not all the analyzers do this, which is
            why it can be turned off.

        Why can't we fix the analyzers to strip out that HTML, and not
        generate spurious tokens? That could probably be done, but it
        probably isn't worth while because:

        * ES will weight common words lower, thanks to it's TF-IDF
          algorithms, which judges words based on how often they
          appear in the entire corpus and in the document, so the p
          tokens will be largely ignored.
        * The pre-l10n search code did it this way, so it doesn't
          break search.
        * When implementing l10n search, I wanted to minimize the
          number of changes needed, and this seemed like an unneeded
          change.
        """

        search = es_utils.Sphilastic(DocumentMappingType)
        search = search.filter(document_locale=locale)
        facet_filter = search._process_filters([('document_locale', locale)])
        search = search.facet_raw(tokens={
            'terms': {'field': 'document_content'},
            'facet_filter': facet_filter})
        facets = search.facet_counts()

        expected = set(expected_tokens)
        if p_tag:
            # Since `expected` is a set, there is no problem adding this
            # twice, since duplicates will be ignored.
            expected.add(u'p')
        actual = set(t['term'] for t in facets['tokens'])
        eq_(actual, expected)

    # These 5 languages were chosen for tokenization testing because
    # they represent the 5 kinds of languages we have: English, Snowball
    # supported languages, ES supported languages, Languages with custom
    # analyzers, and languages with no analyzer, which use the standard
    # analyzer.

    def test_english_tokenization(self):
        """Test that English stemming and stop words work."""
        self._check_locale_tokenization('en-US', ['i', 'have', 'cat'])

    def test_spanish_tokenization(self):
        """Test that Spanish stemming and stop words work."""
        self._check_locale_tokenization('es', ['tien', 'un', 'gat'])

    def test_arabic_tokenization(self):
        """Test that Arabic stemming works.

        I don't read Arabic, this is just what ES gave me when I asked
        it to analyze an Arabic text as Arabic. If someone who reads
        Arabic can improve this test, go for it!
        """
        self._check_locale_tokenization('ar', [u'لد', u'اثن', u'قطط'])

    def test_burmese_tokenization(self):
        """Test that the shingle analyzer is active for Burmese."""
        tokens = [u'အန', u'နု', u'ုပ', u'ပည', u'ညာ']
        self._check_locale_tokenization('my', tokens, False)

    def test_herbrew_tokenization(self):
        """Test that Hebrew uses the standard analyzer."""
        tokens = [u'גאולוגיה', u'היא', u'אחד']
        self._check_locale_tokenization('he', tokens)
