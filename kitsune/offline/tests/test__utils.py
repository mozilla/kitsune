# -*- coding: utf-8 -*-
import time

from nose.tools import eq_

from kitsune.offline import utils
from kitsune.products.tests import product, topic
from kitsune.sumo.tests import TestCase
from kitsune.wiki.tests import document, revision


def _create_doc(title='', product=None, topic=None, is_archived=False):
    title = 'test ' + title if title else 'test'
    doc = document(title=title, save=True, is_archived=is_archived)
    revision(summary='summary', is_approved=True, document=doc, save=True)

    if is_archived:
        expected = {
            'key': 'en-US~' + doc.slug,
            'title': doc.title,
            'archived': True,
            'slug': doc.slug
        }
    else:
        updated = time.mktime(doc.current_revision.created.timetuple())
        expected = {
            'key': 'en-US~' + doc.slug,
            'title': title,
            'html': doc.html,
            'updated': updated,
            'slug': doc.slug,
            'id': doc.id,
            'archived': False
        }

    if product:
        doc.products.add(product)

    if topic:
        doc.topics.add(topic)

    return doc, expected


def _create_product_bundle(prefix='moo'):
    p = product(title=prefix + 'firefox', save=True)
    t1 = topic(title=prefix + 'topic1', product=p, save=True)
    t2 = topic(title=prefix + 'topic2', product=p, save=True)

    doc1, expected_doc1 = _create_doc(title=prefix + 'doc1',
                                      product=p, topic=t1)
    doc2, expected_doc2 = _create_doc(title=prefix + 'doc2',
                                      product=p, topic=t2)

    expected_locale_doc = {
        'key': u'en-US',
        'name': u'English',
        'products': [{
            'slug': p.slug,
            'name': p.title
        }]
    }

    expected_topic1 = {
        'key': 'en-US~' + p.slug + '~' + t1.slug,
        'name': t1.title,
        'docs': [doc1.slug],
        'product': p.slug,
        'slug': t1.slug,
        'children': []
    }

    expected_topic2 = {
        'key': 'en-US~' + p.slug + '~' + t2.slug,
        'name': t2.title,
        'docs': [doc2.slug],
        'product': p.slug,
        'slug': t2.slug,
        'children': []
    }

    return p, {
        'doc1': expected_doc1,
        'doc2': expected_doc2,
        'locale': expected_locale_doc,
        'topic1': expected_topic1,
        'topic2': expected_topic2
    }


class OfflineWikiDataGenerationTest(TestCase):
    def test_serialize_document(self):
        doc, expected = _create_doc()
        serialized = utils.serialize_document_for_offline(doc)
        eq_(expected, serialized)

    def test_serialized_archived_document(self):
        doc, expected = _create_doc(is_archived=True)
        serialized = utils.serialize_document_for_offline(doc)
        eq_(expected, serialized)

    def test_bundle_for_product(self):
        p, expected_bundle = _create_product_bundle()

        bundle = utils.bundle_for_product(p, 'en-US')

        assert 'locales' in bundle
        eq_(1, len(bundle['locales']))
        eq_(expected_bundle['locale'], bundle['locales'].values()[0])

        assert 'topics' in bundle
        eq_(2, len(bundle['topics']))
        topics = sorted(bundle['topics'].values(), key=lambda t: t['slug'])
        eq_(expected_bundle['topic1'], topics[0])
        eq_(expected_bundle['topic2'], topics[1])

        assert 'docs' in bundle
        docs = sorted(bundle['docs'].values(), key=lambda d: d['title'])
        eq_(expected_bundle['doc1'], docs[0])
        eq_(expected_bundle['doc2'], docs[1])

        assert 'indexes' in bundle
        eq_(1, len(bundle['indexes']))
        assert 'en-US~moofirefox' in bundle['indexes']
        assert 'index' in bundle['indexes']['en-US~moofirefox']
        eq_(u'en-US~moofirefox', bundle['indexes']['en-US~moofirefox']['key'])

    def test_merge_bundles(self):
        p1, expected_bundle1 = _create_product_bundle()
        p2, expected_bundle2 = _create_product_bundle('yay')

        bundle1 = utils.bundle_for_product(p1, 'en-US')
        bundle2 = utils.bundle_for_product(p2, 'en-US')

        merged = utils.merge_bundles(bundle1, bundle2)

        assert 'locales' in merged
        eq_(1, len(merged['locales']))

        expected_locale = expected_bundle1['locale']
        expected_locale['products'] += expected_bundle2['locale']['products']

        eq_(expected_locale, merged['locales'][0])

        assert 'topics' in merged
        eq_(4, len(merged['topics']))

        merged['topics'].sort(key=lambda t: t['slug'])

        eq_(expected_bundle1['topic1'], merged['topics'][0])
        eq_(expected_bundle1['topic2'], merged['topics'][1])
        eq_(expected_bundle2['topic1'], merged['topics'][2])
        eq_(expected_bundle2['topic2'], merged['topics'][3])

        assert 'docs' in merged
        eq_(4, len(merged['docs']))

        merged['docs'].sort(key=lambda d: d['title'])

        eq_(expected_bundle1['doc1'], merged['docs'][0])
        eq_(expected_bundle1['doc2'], merged['docs'][1])
        eq_(expected_bundle2['doc1'], merged['docs'][2])
        eq_(expected_bundle2['doc2'], merged['docs'][3])

        eq_(2, len(merged['indexes']))
        merged['indexes'].sort(key=lambda i: i['key'])
        eq_('en-US~moofirefox', merged['indexes'][0]['key'])
        eq_('en-US~yayfirefox', merged['indexes'][1]['key'])

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

    def test_archived_articles_in_bundle(self):
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

    def test_redirect_articles_in_bundle(self):
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

    def test_bogus_articles_in_bundle(self):
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
