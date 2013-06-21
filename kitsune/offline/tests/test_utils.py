# -*- coding: utf-8 -*-
import time

from nose.tools import eq_

from kitsune.offline import utils
from kitsune.products.tests import product, topic
from kitsune.sumo.tests import TestCase
from kitsune.wiki.tests import document, revision


class OfflineWikiDataGenerationTest(TestCase):
    def test_serialize_document(self):
        doc = document(title='test', save=True)
        revision(summary='summary',
                 is_approved=True,
                 document=doc,
                 save=True)

        serialized = utils.serialize_document_for_offline(doc)
        eq_('test', serialized['title'])
        eq_('en-US~' + doc.slug, serialized['key'])
        eq_(doc.html, serialized['html'])
        eq_(doc.slug, serialized['slug'])
        eq_(doc.id, serialized['id'])
        eq_(time.mktime(doc.current_revision.created.timetuple()),
            serialized['updated'])

    def test_serialized_archived_document(self):
        doc = document(title='archived', is_archived=True, save=True)
        revision(is_approved=True, document=doc, save=True)

        serialized = utils.serialize_document_for_offline(doc)
        eq_('archived', serialized['title'])
        eq_('en-US~' + doc.slug, serialized['key'])
        eq_(True, serialized['archived'])
        eq_(doc.slug, serialized['slug'])

    def test_bundle_for_product(self):
        p = product(title='firefox', save=True)
        t1 = topic(title='topic1', product=p, save=True)
        t2 = topic(title='topic2', product=p, save=True)

        doc = document(title='some document', locale='en-US', save=True)
        revision(is_approved=True, document=doc, save=True)
        doc.products.add(p)
        doc.topics.add(t1)

        doc2 = document(title='some other document', locale='en-US', save=True)
        revision(is_approved=True, document=doc2, save=True)

        doc2.products.add(p)
        doc2.topics.add(t2)

        bundle = utils.bundle_for_product(p, 'en-US')
        assert 'locales' in bundle
        eq_(1, len(bundle['locales']))

        locale_doc = bundle['locales'].values()[0]
        locale_doc['children'].sort()

        expected_locale_doc = {
            'key': u'en-US',
            'name': u'English',
            'children': [u'topic1', u'topic2'],
            'products': [{'slug': u'firefox', 'name': u'firefox'}]
        }

        eq_(expected_locale_doc, locale_doc)
        assert 'topics' in bundle
        eq_(2, len(bundle['topics']))
        topics = sorted(bundle['topics'].values(), key=lambda t: t['slug'])

        expected_topic1 = {
            'key': u'en-US~firefox~topic1',
            'name': u'topic1',
            'children': [],
            'docs': [u'some-document'],
            'product': u'firefox',
            'slug': u'topic1'
        }

        expected_topic2 = {
            'key': u'en-US~firefox~topic2',
            'name': u'topic2',
            'children': [],
            'docs': [u'some-other-document'],
            'product': u'firefox',
            'slug': u'topic2'
        }

        eq_(expected_topic1, topics[0])
        eq_(expected_topic2, topics[1])

        assert 'docs' in bundle

        docs = sorted(bundle['docs'].values(), key=lambda d: d['title'])

        expected_doc1 = {
            'key': u'en-US~some-document',
            'title': u'some document',
            'html': doc.html,
            'updated': time.mktime(doc.current_revision.created.timetuple()),
            'slug': u'some-document',
            'id': doc.id
        }

        expected_doc2 = {
            'key': u'en-US~some-other-document',
            'title': u'some other document',
            'html': doc2.html,
            'updated': time.mktime(doc2.current_revision.created.timetuple()),
            'slug': u'some-other-document',
            'id': doc2.id
        }

        eq_(expected_doc1, docs[0])
        eq_(expected_doc2, docs[1])

        assert 'indexes' in bundle
        eq_(1, len(bundle['indexes']))
        assert 'en-US~firefox' in bundle['indexes']
        assert 'index' in bundle['indexes']['en-US~firefox']
        eq_(u'en-US~firefox', bundle['indexes']['en-US~firefox']['key'])

    def test_merge_bundles(self):
        p = product(title='firefox', save=True)
        p2 = product(title='firefox os', save=True)
        t1 = topic(title='topic1', product=p, save=True)
        t2 = topic(title='topic2', product=p2, save=True)

        doc = document(title='test document', locale='en-US', save=True)
        revision(is_approved=True, document=doc, save=True)

        doc.products.add(p)
        doc.topics.add(t1)

        doc2 = document(title='test document2', locale='en-US', save=True)
        revision(is_approved=True, document=doc2, save=True)

        doc2.products.add(p2)
        doc2.topics.add(t2)

        bundle1 = utils.bundle_for_product(p, 'en-US')
        bundle2 = utils.bundle_for_product(p2, 'en-US')

        merged = utils.merge_bundles(bundle1, bundle2)
        assert 'locales' in merged
        assert 'topics' in merged
        assert 'docs' in merged
        assert 'indexes' in merged

        eq_(1, len(merged['locales']))

        expected_locale_doc = {
            'key': u'en-US',
            'name': u'English',
            'children': [u'topic1', u'topic2'],
            'products': [
                {'slug': u'firefox', 'name': u'firefox'},
                {'slug': u'firefox-os', 'name': u'firefox os'}
            ]
        }

        eq_(expected_locale_doc, merged['locales'][0])

        eq_(2, len(merged['topics']))
        merged['topics'].sort(key=lambda t: t['slug'])

        expected_topic1 = {
            'key': u'en-US~firefox~topic1',
            'name': u'topic1',
            'children': [],
            'docs': [u'test-document'],
            'product': u'firefox',
            'slug': u'topic1'
        }

        expected_topic2 = {
            'key': u'en-US~firefox-os~topic2',
            'name': u'topic2',
            'children': [],
            'docs': [u'test-document2'],
            'product': u'firefox-os',
            'slug': u'topic2'
        }

        eq_(expected_topic1, merged['topics'][0])
        eq_(expected_topic2, merged['topics'][1])

        eq_(2, len(merged['docs']))
        merged['docs'].sort(key=lambda d: d['title'])

        expected_doc1 = {
            'key': u'en-US~test-document',
            'title': u'test document',
            'html': doc.html,
            'updated': time.mktime(doc.current_revision.created.timetuple()),
            'slug': u'test-document',
            'id': doc.id
        }

        expected_doc2 = {
            'key': u'en-US~test-document2',
            'title': u'test document2',
            'html': doc2.html,
            'updated': time.mktime(doc2.current_revision.created.timetuple()),
            'slug': u'test-document2',
            'id': doc2.id
        }

        eq_(expected_doc1, merged['docs'][0])
        eq_(expected_doc2, merged['docs'][1])

        eq_(2, len(merged['indexes']))
        merged['indexes'].sort(key=lambda i: i['key'])
        eq_('en-US~firefox', merged['indexes'][0]['key'])
        eq_('en-US~firefox-os', merged['indexes'][1]['key'])


    def test_index_generation(self):
        p = product(title='firefox', save=True)
        t = topic(title='topic1', product=p, save=True)

        doc = document(title='firefox bookmarks',
                       locale='en-US', save=True)

        revision(is_approved=True,
                 summary='this is an article about firefox bookmarks',
                 document=doc, save=True)

        doc.products.add(p)
        doc.topics.add(t)

        doc2 = document(title='private browsing',
                        locale='en-US', save=True)

        revision(is_approved=True,
                 summary='this is an article about private browsing',
                 document=doc2, save=True)

        doc2.products.add(p)
        doc2.topics.add(t)

        bundle = utils.bundle_for_product(p, 'en-US')
        index = bundle['indexes']['en-US~firefox']['index']

        words_in_both = ('this', 'is', 'an', 'article', 'about')

        for word in words_in_both:
            assert word in index
            eq_(2, len(index[word]))
            eq_(2, len(index[word][0]))
            eq_(2, len(index[word][1]))

        assert 'firefox' in index
        eq_(1, len(index['firefox']))
        # Yeah. 'firefox' in this corpus _better_ score higher than 'this'.
        assert index['firefox'][0][1] > index['this'][0][1]

        assert 'bookmarks' in index
        eq_(1, len(index['bookmarks']))
        assert index['bookmarks'][0][1] > index['this'][0][1]

        assert 'private' in index
        eq_(1, len(index['private']))
        assert index['private'][0][1] > index['this'][0][1]

        assert 'browsing' in index
        eq_(1, len(index['browsing']))
        assert index['browsing'][0][1] > index['this'][0][1]

    def test_archived_articles(self):
        p = product(title='firefox', save=True)
        t1 = topic(title='topic1', product=p, save=True)

        doc = document(title='test', is_archived=True,
                       locale='en-US', save=True)
        revision(is_approved=True, document=doc, save=True)
        doc.products.add(p)
        doc.topics.add(t1)

        bundle = utils.bundle_for_product(p, 'en-US')
        eq_(1, len(bundle['docs']))
        doc = bundle['docs'].values()[0]
        eq_(True, doc['archived'])
        assert 'html' not in doc
        eq_(1, len(bundle['topics']))

    def test_redirect_articles(self):
        p = product(title='firefox', save=True)
        t1 = topic(title='topic1', product=p, save=True)

        doc = document(title='test2', locale='en-US', save=True)
        revision(is_approved=True,
                 document=doc,
                 save=True)

        doc.products.add(p)
        doc.topics.add(t1)

        doc = document(title='test', locale='en-US', save=True)
        revision(is_approved=True, document=doc, content=u'REDIRECT [[doc2]]',
                 save=True)

        doc.products.add(p)
        doc.topics.add(t1)

        bundle = utils.bundle_for_product(p, 'en-US')
        eq_(1, len(bundle['docs']))
        doc = bundle['docs'].values()[0]
        eq_('test2', doc['title'])

    def test_bogus_articles(self):
        p = product(title='firefox', save=True)
        topic(title='topic1', product=p, save=True)

        # Document with no revision should be fun
        doc = document(title='test2', locale='en-US', save=True)

        bundle = utils.bundle_for_product(p, 'en-US')
        eq_(0, len(bundle['docs']))
        eq_(0, len(bundle['topics']))

        # article with no html.
        revision(document=doc, content='', save=True)
        bundle = utils.bundle_for_product(p, 'en-US')
        eq_(0, len(bundle['docs']))
        eq_(0, len(bundle['topics']))

    def test_other_languages(self):
        p = product(title='firefox', save=True)
        t1 = topic(title='topic1', product=p, save=True)

        doc = document(title='test', locale='en-US', save=True)
        revision(is_approved=True, document=doc, save=True)

        doc.products.add(p)
        doc.topics.add(t1)

        translated_doc = document(title=u'测试', locale='zh-CN', parent=doc,
                                  save=True)
        revision(is_approved=True, document=translated_doc, save=True)

        bundle = utils.bundle_for_product(p, 'zh-CN')
        eq_(1, len(bundle['docs']))

        doc = bundle['docs'].values()[0]
        eq_(u'测试', doc['title'])

    # disabled as it is not exactly clear what we ant to do with this... yet
    #def test_east_asian_language_article_indexes(self):
    #    # These should use a different algorithm for parsing for the index.
    #    p = product(title='firefox', save=True)
    #    t1 = topic(title='topic1', product=p, save=True)
    #
    #    doc = document(title='test', locale='en-US', save=True)
    #    revision(is_approved=True, document=doc, save=True)
    #
    #    doc.products.add(p)
    #    doc.topics.add(t1)
    #
    #    translated_doc = document(title=u'书签', locale='zh-CN', parent=doc,
    #                              save=True)
    #    revision(is_approved=True, summary=u'这项目的开发员看不懂这个！:D',
    #             document=translated_doc, save=True)