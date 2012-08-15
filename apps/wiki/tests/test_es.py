from nose.tools import eq_

from products.tests import product
from search.tests.test_es import ElasticTestCase
from topics.tests import topic
from wiki.tests import document, revision
from wiki.models import Document
from wiki.config import REDIRECT_CONTENT


class TestPostUpdate(ElasticTestCase):
    def test_add_and_delete(self):
        """Adding a doc should add it to the search index; deleting should
        delete it."""
        doc = document(save=True)
        revision(document=doc, is_approved=True, save=True)
        self.refresh()
        eq_(Document.search().count(), 1)

        doc.delete()
        self.refresh()
        eq_(Document.search().count(), 0)

    def test_translations_get_parent_tags(self):
        doc1 = document(title=u'Audio too loud')
        doc1.save()
        revision(document=doc1, is_approved=True, save=True)
        doc1.topics.add(topic(slug='cookies', save=True))
        doc1.topics.add(topic(slug='general', save=True))
        doc1.products.add(product(slug='desktop', save=True))

        doc2 = document(title=u'Audio too loud bork bork',
                        parent=doc1)
        doc2.save()
        revision(document=doc2, is_approved=True, save=True)
        doc2.tags.add(u'badtag')

        # Verify the parent has the right tags.
        doc_dict = Document.extract_document(doc1.id)
        eq_(doc_dict['document_topic'], [u'cookies', u'general'])
        eq_(doc_dict['document_product'], [u'desktop'])

        # Verify the translation has the parent's tags.
        doc_dict = Document.extract_document(doc2.id)
        eq_(doc_dict['document_topic'], [u'cookies', u'general'])
        eq_(doc_dict['document_product'], [u'desktop'])

    def test_wiki_topics(self):
        """Make sure that adding topics to a Document causes it to
        refresh the index.

        """
        t = topic(slug=u'hiphop', save=True)
        eq_(Document.search().filter(document_topic=t.slug).count(), 0)
        doc = document(save=True)
        revision(document=doc, is_approved=True, save=True)
        self.refresh()
        eq_(Document.search().filter(document_topic=t.slug).count(), 0)
        doc.topics.add(t)
        self.refresh()
        eq_(Document.search().filter(document_topic=t.slug).count(), 1)
        doc.topics.clear()
        self.refresh()

        # Make sure the document itself is still there and that we didn't
        # accidentally delete it through screwed up signal handling:
        eq_(Document.search().filter().count(), 1)

        eq_(Document.search().filter(document_topic=t.slug).count(), 0)

    def test_wiki_products(self):
        """Make sure that adding products to a Document causes it to
        refresh the index.

        """
        p = product(slug=u'desktop', save=True)
        eq_(Document.search().filter(document_product=p.slug).count(), 0)
        doc = document(save=True)
        revision(document=doc, is_approved=True, save=True)
        self.refresh()
        eq_(Document.search().filter(document_product=p.slug).count(), 0)
        doc.products.add(p)
        self.refresh()
        eq_(Document.search().filter(document_product=p.slug).count(), 1)
        doc.products.remove(p)
        self.refresh()

        # Make sure the document itself is still there and that we didn't
        # accidentally delete it through screwed up signal handling:
        eq_(Document.search().filter().count(), 1)

        eq_(Document.search().filter(document_product=p.slug).count(), 0)

    def test_wiki_no_revisions(self):
        """Don't index documents without approved revisions"""
        # Create a document with no revisions and make sure the
        # document is not in the index.
        doc = document(save=True)
        self.refresh()
        eq_(Document.search().count(), 0)
        # Create a revision that's not approved and make sure the
        # document is still not in the index.
        revision(document=doc, is_approved=False, save=True)
        self.refresh()
        eq_(Document.search().count(), 0)

    def test_wiki_redirects(self):
        """Make sure we don't index redirects"""
        # First create a revision that doesn't have a redirect and
        # make sure it's in the index.
        doc = document(title=u'wool hats')
        doc.save()
        revision(document=doc, is_approved=True, save=True)
        self.refresh()
        eq_(Document.search().query('wool').count(), 1)

        # Now create a revision that is a redirect and make sure the
        # document is removed from the index.
        revision(document=doc, content=REDIRECT_CONTENT, is_approved=True,
                 save=True)
        self.refresh()
        eq_(Document.search().query('wool').count(), 0)

    def test_wiki_keywords(self):
        """Make sure updating keywords updates the index."""
        # Create a document with a revision with no keywords. It
        # shouldn't show up with a document_keywords term query for
        # 'wool' since it has no keywords.
        doc = document(title=u'wool hats')
        doc.save()
        revision(document=doc, is_approved=True, save=True)
        self.refresh()
        eq_(Document.search().query(document_keywords='wool').count(), 0)

        revision(document=doc, is_approved=True, keywords='wool', save=True)
        self.refresh()

        eq_(Document.search().query(document_keywords='wool').count(), 1)
