import json
from datetime import datetime, timedelta

from django.contrib.contenttypes.models import ContentType

from nose.tools import eq_

from kitsune import search as constants
from kitsune.access.tests import PermissionFactory
from kitsune.forums.tests import ForumFactory, PostFactory, RestrictedForumFactory, ThreadFactory
from kitsune.products.tests import ProductFactory, TopicFactory
from kitsune.questions.tests import (
    QuestionFactory, AnswerFactory, AnswerVoteFactory, QuestionVoteFactory)
from kitsune.search.tests.test_es import ElasticTestCase
from kitsune.sumo.tests import LocalizingClient
from kitsune.sumo.urlresolvers import reverse
from kitsune.users.tests import GroupFactory, UserFactory
from kitsune.wiki.tests import (
    DocumentFactory, ApprovedRevisionFactory, RevisionFactory, HelpfulVoteFactory)


class AdvancedSearchTests(ElasticTestCase):
    client_class = LocalizingClient

    def test_json_format(self):
        """JSON without callback should return application/json"""
        response = self.client.get(reverse('search'), {
            'q': 'bookmarks',
            'a': '1',
            'format': 'json',
        }, follow=True)
        eq_(response.status_code, 200)
        eq_(response['Content-Type'], 'application/json')

    def test_json_callback_validation(self):
        """Various json callbacks -- validation"""
        response = self.client.get(reverse('search'), {
            'q': 'bookmarks',
            'a': '1',
            'format': 'json',
            'callback': 'callback',
        }, follow=True)
        eq_(response.status_code, 200)
        eq_(response['Content-Type'], 'application/x-javascript')

    def test_json_empty_query_a_1(self):
        """Empty query returns JSON format"""
        response = self.client.get(reverse('search'), {
            'format': 'json', 'a': 1,
        }, follow=True)
        eq_(response.status_code, 200)
        eq_(response['Content-Type'], 'application/json')

    def test_json_empty_query_a_2(self):
        """Empty query asking for form returns 400"""
        # Test with flags for advanced search or not
        response = self.client.get(reverse('search'), {
            'format': 'json', 'a': 2,
        }, follow=True)
        eq_(response.status_code, 400)
        eq_(response['Content-Type'], 'application/json')

    def test_search_products(self):
        p = ProductFactory(title='Product One', slug='product')
        doc = DocumentFactory(title='cookies', locale='en-US', category=10, products=[p])
        RevisionFactory(document=doc, is_approved=True)

        self.refresh()

        response = self.client.get(
            reverse('search.advanced'),
            {'a': '1', 'product': 'product', 'q': 'cookies', 'w': '1'})

        assert "We couldn't find any results for" not in response.content
        eq_(200, response.status_code)
        assert 'Product One' in response.content

    def test_search_multiple_products(self):
        p1 = ProductFactory(title='Product One', slug='product-one', display_order=1)
        p2 = ProductFactory(title='Product Two', slug='product-two', display_order=2)
        doc1 = DocumentFactory(title='cookies', locale='en-US', category=10, products=[p1, p2])
        RevisionFactory(document=doc1, is_approved=True)

        self.refresh()

        response = self.client.get(reverse('search.advanced'), {
            'a': '1',
            'product': ['product-one', 'product-two'],
            'q': 'cookies',
            'w': '1',
        })

        eq_(200, response.status_code)
        assert "We couldn't find any results for" not in response.content
        assert 'Product One, Product Two' in response.content

    def test_wiki_no_query(self):
        """Tests advanced search with no query"""
        doc = DocumentFactory(locale='en-US', category=10)
        doc.tags.add('desktop')
        RevisionFactory(document=doc, is_approved=True)

        self.refresh()

        response = self.client.get(reverse('search.advanced'), {
            'q': '', 'tags': 'desktop', 'w': '1', 'a': '1',
            'format': 'json'
        })

        eq_(200, response.status_code)

        content = json.loads(response.content)
        eq_(content['total'], 1)

    def test_questions_sortby(self):
        """Tests advanced search for questions with a sortby"""
        QuestionFactory(title='tags tags tags')

        self.refresh()

        # Advanced search for questions with sortby set to 3 which is
        # '-replies' which is different between Sphinx and ES.
        response = self.client.get(reverse('search.advanced'), {
            'q': 'tags', 'tags': 'desktop', 'w': '2', 'a': '1', 'sortby': '3',
            'format': 'json'
        })

        eq_(200, response.status_code)

        content = json.loads(response.content)
        eq_(content['total'], 1)

    def test_sortby_documents_helpful(self):
        """Tests advanced search with a sortby_documents by helpful"""
        r1 = RevisionFactory(is_approved=True)
        r2 = RevisionFactory(is_approved=True)
        HelpfulVoteFactory(revision=r2, helpful=True)

        # Note: We have to wipe and rebuild the index because new
        # helpful_votes don't update the index data.
        self.setup_indexes()
        self.reindex_and_refresh()

        # r2.document should come first with 1 vote.
        response = self.client.get(reverse('search.advanced'), {
            'w': '1', 'a': '1', 'sortby_documents': 'helpful',
            'format': 'json'
        })
        eq_(200, response.status_code)

        content = json.loads(response.content)
        eq_(r2.document.title, content['results'][0]['title'])

        # Vote twice on r1, now it should come first.
        HelpfulVoteFactory(revision=r1, helpful=True)
        HelpfulVoteFactory(revision=r1, helpful=True)

        self.setup_indexes()
        self.reindex_and_refresh()

        response = self.client.get(reverse('search.advanced'), {
            'w': '1', 'a': '1', 'sortby_documents': 'helpful',
            'format': 'json'})
        eq_(200, response.status_code)

        content = json.loads(response.content)
        eq_(r1.document.title, content['results'][0]['title'])

    def test_questions_num_votes(self):
        """Tests advanced search for questions num_votes filter"""
        q = QuestionFactory(title='tags tags tags')

        # Add two question votes
        QuestionVoteFactory(question=q)
        QuestionVoteFactory(question=q)

        self.refresh()

        # Advanced search for questions with num_votes > 5. The above
        # question should be not in this set.
        response = self.client.get(reverse('search.advanced'), {
            'q': '', 'tags': 'desktop', 'w': '2', 'a': '1',
            'num_voted': 2, 'num_votes': 5,
            'format': 'json'
        })

        eq_(200, response.status_code)

        content = json.loads(response.content)
        eq_(content['total'], 0)

        # Advanced search for questions with num_votes < 1. The above
        # question should be not in this set.
        response = self.client.get(reverse('search.advanced'), {
            'q': '', 'tags': 'desktop', 'w': '2', 'a': '1',
            'num_voted': 1, 'num_votes': 1,
            'format': 'json'
        })

        eq_(200, response.status_code)

        content = json.loads(response.content)
        eq_(content['total'], 0)

    def test_num_votes_none(self):
        """Tests num_voted filtering where num_votes is ''"""
        q = QuestionFactory()
        QuestionVoteFactory(question=q)

        self.refresh()

        qs = {'q': '', 'w': 2, 'a': 1, 'num_voted': 2, 'num_votes': ''}
        response = self.client.get(reverse('search.advanced'), qs)
        eq_(200, response.status_code)

    def test_forums_search(self):
        """This tests whether forum posts show up in searches"""
        thread1 = ThreadFactory(title='crash')
        PostFactory(thread=thread1)

        self.refresh()

        response = self.client.get(reverse('search.advanced'), {
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
        forum1 = ForumFactory(name='ou812forum')
        thread1 = ThreadFactory(forum=forum1)
        PostFactory(thread=thread1, content='audio')

        forum2 = RestrictedForumFactory(name='restrictedkeepout')
        thread2 = ThreadFactory(forum=forum2)
        PostFactory(thread=thread2, content='audio restricted')

        self.refresh()

        # Do a search as an anonymous user but don't specify the
        # forums to filter on. Should only see one of the posts.
        response = self.client.get(reverse('search.advanced'), {
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
        u = UserFactory()
        g = GroupFactory()
        g.user_set.add(u)
        ct = ContentType.objects.get_for_model(forum2)
        PermissionFactory(
            codename='forums_forum.view_in_forum',
            content_type=ct,
            object_id=forum2.id,
            group=g)

        self.client.login(username=u.username, password='testpass')
        response = self.client.get(reverse('search.advanced'), {
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
        forum1 = ForumFactory(name='ou812forum')
        thread1 = ThreadFactory(forum=forum1)
        PostFactory(thread=thread1, content='audio')

        forum2 = RestrictedForumFactory(name='restrictedkeepout')
        thread2 = ThreadFactory(forum=forum2)
        PostFactory(thread=thread2, content='audio restricted')

        self.refresh()

        # Do a search as an anonymous user and specify both
        # forums. Should only see the post from the unrestricted
        # forum.
        response = self.client.get(reverse('search.advanced'), {
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
        u = UserFactory()
        g = GroupFactory()
        g.user_set.add(u)
        ct = ContentType.objects.get_for_model(forum2)
        PermissionFactory(
            codename='forums_forum.view_in_forum',
            content_type=ct,
            object_id=forum2.id,
            group=g)

        self.client.login(username=u.username, password='testpass')
        response = self.client.get(reverse('search.advanced'), {
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
        thread1 = ThreadFactory(title='crash', created=post_created_ds)
        PostFactory(thread=thread1, created=(post_created_ds + timedelta(hours=1)))

        self.refresh()

        # The thread/post should not show up in results for items
        # created AFTER 1/12/2010.
        response = self.client.get(reverse('search.advanced'), {
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
        response = self.client.get(reverse('search.advanced'), {
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
        response = self.client.get(reverse('search.advanced'), {
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
        response = self.client.get(reverse('search.advanced'), {
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
        ques = QuestionFactory(title='audio')
        ques.tags.add('Windows 7')

        self.refresh()

        response = self.client.get(reverse('search.advanced'), {
            'q': 'audio', 'q_tags': 'Windows 7', 'w': '2', 'a': '1',
            'sortby': '0', 'format': 'json'
        })

        eq_(200, response.status_code)

        content = json.loads(response.content)
        eq_(content['total'], 1)

    def test_category_invalid(self):
        """Tests passing an invalid category"""
        # wiki and questions
        ques = QuestionFactory(title='q1 audio')
        ques.tags.add('desktop')
        ans = AnswerFactory(question=ques)
        AnswerVoteFactory(answer=ans, helpful=True)

        d1 = DocumentFactory(
            title='d1 audio',
            locale='en-US',
            category=10,
            is_archived=False,
            tags=['desktop'])
        ApprovedRevisionFactory(document=d1)

        self.refresh()

        qs = {'a': 1, 'w': 3, 'format': 'json', 'category': 'invalid'}
        response = self.client.get(reverse('search.advanced'), qs)
        eq_(2, json.loads(response.content)['total'])

    def test_created(self):
        """Basic functionality of created filter."""
        created_ds = datetime(2010, 6, 19, 12, 00)

        # on 6/19/2010
        q1 = QuestionFactory(title='q1 audio', created=created_ds)
        q1.tags.add('desktop')
        ans = AnswerFactory(question=q1)
        AnswerVoteFactory(answer=ans, helpful=True)

        # on 6/21/2010
        q2 = QuestionFactory(
            title='q2 audio',
            created=(created_ds + timedelta(days=2)),
            tags=['desktop'])
        ans = AnswerFactory(question=q2)
        AnswerVoteFactory(answer=ans, helpful=True)

        self.refresh()

        qs = {'a': 1, 'w': 2, 'format': 'json',
              'sortby': 2, 'created_date': '06/20/2010'}

        qs['created'] = constants.INTERVAL_BEFORE
        response = self.client.get(reverse('search.advanced'), qs)
        results = json.loads(response.content)['results']
        eq_([q1.get_absolute_url()], [r['url'] for r in results])

        qs['created'] = constants.INTERVAL_AFTER
        response = self.client.get(reverse('search.advanced'), qs)
        results = json.loads(response.content)['results']
        eq_([q2.get_absolute_url()], [r['url'] for r in results])

    def test_sortby_invalid(self):
        """Invalid created_date is ignored."""
        qs = {'a': 1, 'w': 4, 'format': 'json', 'sortby': ''}
        response = self.client.get(reverse('search.advanced'), qs)
        eq_(200, response.status_code)

    def test_created_date_invalid(self):
        """Invalid created_date is ignored."""
        thread1 = ThreadFactory()
        PostFactory(thread=thread1)

        self.refresh()

        qs = {'a': 1, 'w': 4, 'format': 'json',
              'created': constants.INTERVAL_AFTER,
              'created_date': 'invalid'}
        response = self.client.get(reverse('search.advanced'), qs)
        eq_(1, json.loads(response.content)['total'])

    def test_created_date_nonexistent(self):
        """created is set while created_date is left out of the query."""
        qs = {'a': 1, 'w': 2, 'format': 'json', 'created': 1}
        response = self.client.get(reverse('search.advanced'), qs)
        eq_(200, response.status_code)

    def test_updated_invalid(self):
        """Invalid updated_date is ignored."""
        thread1 = ThreadFactory()
        PostFactory(thread=thread1)

        self.refresh()

        qs = {'a': 1, 'w': 4, 'format': 'json',
              'updated': 1, 'updated_date': 'invalid'}
        response = self.client.get(reverse('search.advanced'), qs)
        eq_(1, json.loads(response.content)['total'])

    def test_updated_nonexistent(self):
        """updated is set while updated_date is left out of the query."""
        thread1 = ThreadFactory()
        PostFactory(thread=thread1)

        self.refresh()

        qs = {'a': 1, 'w': 2, 'format': 'json', 'updated': 1}
        response = self.client.get(reverse('search.advanced'), qs)
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
            u = UserFactory(username=name)
            for i in range(number):
                ques = QuestionFactory(title='audio', creator=u)
                ques.tags.add('desktop')
                ans = AnswerFactory(question=ques)
                AnswerVoteFactory(answer=ans, helpful=True)

        self.refresh()

        qs = {'a': 1, 'w': 2, 'format': 'json'}

        for author, total in author_vals:
            qs.update({'asked_by': author})
            response = self.client.get(reverse('search.advanced'), qs)
            eq_(total, json.loads(response.content)['total'])

    def test_question_topics(self):
        """Search questions for topics."""
        p = ProductFactory()
        t1 = TopicFactory(slug='doesnotexist', product=p)
        t2 = TopicFactory(slug='cookies', product=p)
        t3 = TopicFactory(slug='sync', product=p)

        QuestionFactory(topic=t2)
        QuestionFactory(topic=t2)
        QuestionFactory(topic=t3)

        self.refresh()

        topic_vals = (
            (t1.slug, 0),
            (t2.slug, 2),
            (t3.slug, 1),
        )

        qs = {'a': 1, 'w': 2, 'format': 'json'}
        for topics, number in topic_vals:
            qs.update({'topics': topics})
            response = self.client.get(reverse('search.advanced'), qs)
            eq_(number, json.loads(response.content)['total'])

    def test_wiki_topics(self):
        """Search wiki for topics, includes multiple."""
        t1 = TopicFactory(slug='doesnotexist')
        t2 = TopicFactory(slug='extant')
        t3 = TopicFactory(slug='tagged')

        doc = DocumentFactory(locale='en-US', category=10)
        doc.topics.add(t2)
        RevisionFactory(document=doc, is_approved=True)

        doc = DocumentFactory(locale='en-US', category=10)
        doc.topics.add(t2)
        doc.topics.add(t3)
        RevisionFactory(document=doc, is_approved=True)

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
            response = self.client.get(reverse('search.advanced'), qs)
            eq_(number, json.loads(response.content)['total'])

    def test_wiki_topics_inherit(self):
        """Translations inherit topics from their parents."""
        doc = DocumentFactory(locale='en-US', category=10)
        doc.topics.add(TopicFactory(slug='extant'))
        RevisionFactory(document=doc, is_approved=True)

        translated = DocumentFactory(locale='es', parent=doc, category=10)
        RevisionFactory(document=translated, is_approved=True)

        self.refresh()

        qs = {'a': 1, 'w': 1, 'format': 'json', 'topics': 'extant'}
        response = self.client.get(reverse('search.advanced', locale='es'), qs)
        eq_(1, json.loads(response.content)['total'])

    def test_question_products(self):
        """Search questions for products."""
        p1 = ProductFactory(slug='b2g')
        p2 = ProductFactory(slug='mobile')
        p3 = ProductFactory(slug='desktop')

        QuestionFactory(product=p2)
        QuestionFactory(product=p2)
        QuestionFactory(product=p3)

        self.refresh()

        product_vals = (
            (p1.slug, 0),
            (p2.slug, 2),
            (p3.slug, 1),
        )

        qs = {'a': 1, 'w': 2, 'format': 'json'}
        for products, number in product_vals:
            qs.update({'product': products})
            response = self.client.get(reverse('search.advanced'), qs)
            eq_(number, json.loads(response.content)['total'])

    def test_wiki_products(self):
        """Search wiki for products."""

        prod_vals = (
            (ProductFactory(slug='b2g'), 0),
            (ProductFactory(slug='mobile'), 1),
            (ProductFactory(slug='desktop'), 2),
        )

        for prod, total in prod_vals:
            for i in range(total):
                doc = DocumentFactory(locale='en-US', category=10)
                doc.products.add(prod)
                RevisionFactory(document=doc, is_approved=True)

        self.refresh()

        qs = {'a': 1, 'w': 1, 'format': 'json'}

        for prod, total in prod_vals:
            qs.update({'product': prod.slug})
            response = self.client.get(reverse('search.advanced'), qs)
            eq_(total, json.loads(response.content)['total'])

    def test_wiki_products_inherit(self):
        """Translations inherit products from their parents."""
        doc = DocumentFactory(locale='en-US', category=10)
        p = ProductFactory(title='Firefox', slug='desktop')
        doc.products.add(p)
        RevisionFactory(document=doc, is_approved=True)

        translated = DocumentFactory(locale='fr', parent=doc, category=10)
        RevisionFactory(document=translated, is_approved=True)

        self.refresh()

        qs = {'a': 1, 'w': 1, 'format': 'json', 'product': p.slug}
        response = self.client.get(reverse('search.advanced', locale='fr'), qs)
        eq_(1, json.loads(response.content)['total'])

    def test_discussion_filter_author(self):
        """Filter by author in discussion forums."""
        author_vals = (
            ('DoesNotExist', 0),
            ('admin', 1),
            ('jsocol', 4),
        )

        for name, number in author_vals:
            u = UserFactory(username=name)
            for i in range(number):
                thread1 = ThreadFactory(title='audio')
                PostFactory(thread=thread1, author=u)

        self.refresh()

        qs = {'a': 1, 'w': 4, 'format': 'json'}

        for author, total in author_vals:
            qs.update({'author': author})
            response = self.client.get(reverse('search.advanced'), qs)
            eq_(total, json.loads(response.content)['total'])

    def test_discussion_filter_sticky(self):
        """Filter for sticky threads."""
        thread1 = ThreadFactory(title='audio', is_locked=True, is_sticky=True)
        PostFactory(thread=thread1)

        self.refresh()

        qs = {'a': 1, 'w': 4, 'format': 'json', 'thread_type': 1, 'forum': 1}
        response = self.client.get(reverse('search.advanced'), qs)
        results = json.loads(response.content)['results']
        eq_(len(results), 1)

    def test_discussion_filter_locked(self):
        """Filter for locked threads."""
        thread1 = ThreadFactory(title='audio', is_locked=True)
        PostFactory(thread=thread1)

        self.refresh()

        qs = {'a': 1, 'w': 4, 'format': 'json', 'thread_type': 2}
        response = self.client.get(reverse('search.advanced'), qs)
        results = json.loads(response.content)['results']
        eq_(len(results), 1)

    def test_discussion_filter_sticky_locked(self):
        """Filter for locked and sticky threads."""
        thread1 = ThreadFactory(title='audio', is_locked=True, is_sticky=True)
        PostFactory(thread=thread1)

        self.refresh()

        qs = {'a': 1, 'w': 4, 'format': 'json', 'thread_type': (1, 2)}
        response = self.client.get(reverse('search.advanced'), qs)
        result = json.loads(response.content)['results'][0]
        eq_(thread1.get_absolute_url(), result['url'])

    def test_forums_filter_updated(self):
        """Filter for updated date."""
        post_updated_ds = datetime(2010, 5, 3, 12, 00)

        thread1 = ThreadFactory(title='t1 audio')
        PostFactory(thread=thread1, created=post_updated_ds)

        thread2 = ThreadFactory(title='t2 audio')
        PostFactory(thread=thread2, created=(post_updated_ds + timedelta(days=2)))

        self.refresh()

        qs = {'a': 1, 'w': 4, 'format': 'json',
              'sortby': 1, 'updated_date': '05/04/2010'}

        qs['updated'] = constants.INTERVAL_BEFORE
        response = self.client.get(reverse('search.advanced'), qs)
        results = json.loads(response.content)['results']
        eq_([thread1.get_absolute_url()], [r['url'] for r in results])

        qs['updated'] = constants.INTERVAL_AFTER
        response = self.client.get(reverse('search.advanced'), qs)
        results = json.loads(response.content)['results']
        eq_([thread2.get_absolute_url()], [r['url'] for r in results])

    def test_archived(self):
        """Ensure archived articles show only when requested."""
        doc = DocumentFactory(title='impalas', locale='en-US', is_archived=True)
        ApprovedRevisionFactory(document=doc, summary='impalas', is_approved=True)

        self.refresh()

        # include_archived gets the above document
        qs = {'q': 'impalas', 'a': 1, 'w': 1, 'format': 'json',
              'include_archived': 'on'}
        response = self.client.get(reverse('search.advanced'), qs)
        results = json.loads(response.content)['results']
        eq_(1, len(results))

        # no include_archived gets you nothing since the only
        # document in the index is archived
        qs = {'q': 'impalas', 'a': 0, 'w': 1, 'format': 'json'}
        response = self.client.get(reverse('search.advanced'), qs)
        results = json.loads(response.content)['results']
        eq_(0, len(results))

    def test_discussion_filter_forum(self):
        """Filter by forum in discussion forums."""
        forum1 = ForumFactory(name='Forum 1')
        thread1 = ThreadFactory(forum=forum1, title='audio 1')
        PostFactory(thread=thread1)

        forum2 = ForumFactory(name='Forum 2')
        thread2 = ThreadFactory(forum=forum2, title='audio 2')
        PostFactory(thread=thread2)

        self.refresh()

        qs = {'a': 1, 'w': 4, 'format': 'json'}

        for forum_id in (forum1.id, forum2.id):
            qs['forum'] = int(forum_id)
            response = self.client.get(reverse('search.advanced'), qs)
            eq_(json.loads(response.content)['total'], 1)

    def test_discussion_forum_with_restricted_forums(self):
        """Tests who can see restricted forums in search form."""
        # This is a long test, but it saves us from doing the setup
        # twice.
        forum1 = ForumFactory(name='ou812forum')
        thread1 = ThreadFactory(forum=forum1, title='audio 2')
        PostFactory(thread=thread1)

        forum2 = RestrictedForumFactory(name='restrictedkeepout')
        thread2 = ThreadFactory(forum=forum2, title='audio 2')
        PostFactory(thread=thread2)

        self.refresh()

        # Get the Advanced Search Form as an anonymous user
        response = self.client.get(reverse('search.advanced'), {'a': '2'})
        eq_(200, response.status_code)

        # Regular forum should show up
        assert 'ou812forum' in response.content

        # Restricted forum should not show up
        assert 'restrictedkeepout' not in response.content

        u = UserFactory()
        g = GroupFactory()
        g.user_set.add(u)
        ct = ContentType.objects.get_for_model(forum2)
        PermissionFactory(
            codename='forums_forum.view_in_forum',
            content_type=ct,
            object_id=forum2.id,
            group=g)

        # Get the Advanced Search Form as a logged in user
        self.client.login(username=u.username, password='testpass')
        response = self.client.get(reverse('search.advanced'), {'a': '2'})
        eq_(200, response.status_code)

        # Both forums should show up for authorized user
        assert 'ou812forum' in response.content
        assert 'restrictedkeepout' in response.content
