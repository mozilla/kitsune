from datetime import datetime, timedelta

from nose.tools import eq_

from kitsune.products.tests import ProductFactory, TopicFactory
from kitsune.search.tests.test_es import ElasticTestCase
from kitsune.wiki.tests import (
    DocumentFactory, RevisionFactory, HelpfulVoteFactory, RedirectRevisionFactory)
from kitsune.wiki.models import DocumentMappingType, RevisionMetricsMappingType


class DocumentUpdateTests(ElasticTestCase):
    def test_add_and_delete(self):
        """Adding a doc should add it to the search index; deleting should
        delete it."""
        doc = DocumentFactory()
        RevisionFactory(document=doc, is_approved=True)
        self.refresh()
        eq_(DocumentMappingType.search().count(), 1)

        doc.delete()
        self.refresh()
        eq_(DocumentMappingType.search().count(), 0)

    def test_translations_get_parent_tags(self):
        t1 = TopicFactory(display_order=1)
        t2 = TopicFactory(display_order=2)
        p = ProductFactory()
        doc1 = DocumentFactory(
            title='Audio too loud',
            products=[p],
            topics=[t1, t2])
        RevisionFactory(document=doc1, is_approved=True)

        doc2 = DocumentFactory(title='Audio too loud bork bork', parent=doc1, tags=['badtag'])
        RevisionFactory(document=doc2, is_approved=True)

        # Verify the parent has the right tags.
        doc_dict = DocumentMappingType.extract_document(doc1.id)
        eq_(sorted(doc_dict['topic']), sorted([t1.slug, t2.slug]))
        eq_(doc_dict['product'], [p.slug])

        # Verify the translation has the parent's tags.
        doc_dict = DocumentMappingType.extract_document(doc2.id)
        eq_(sorted(doc_dict['topic']), sorted([t1.slug, t2.slug]))
        eq_(doc_dict['product'], [p.slug])

    def test_wiki_topics(self):
        """Make sure that adding topics to a Document causes it to
        refresh the index.

        """
        t = TopicFactory(slug='hiphop')
        eq_(DocumentMappingType.search().filter(topic=t.slug).count(), 0)
        doc = DocumentFactory()
        RevisionFactory(document=doc, is_approved=True)
        self.refresh()
        eq_(DocumentMappingType.search().filter(topic=t.slug).count(), 0)
        doc.topics.add(t)
        self.refresh()
        eq_(DocumentMappingType.search().filter(topic=t.slug).count(), 1)
        doc.topics.clear()
        self.refresh()

        # Make sure the document itself is still there and that we didn't
        # accidentally delete it through screwed up signal handling:
        eq_(DocumentMappingType.search().filter().count(), 1)

        eq_(DocumentMappingType.search().filter(topic=t.slug).count(), 0)

    def test_wiki_products(self):
        """Make sure that adding products to a Document causes it to
        refresh the index.

        """
        p = ProductFactory(slug='desktop')
        eq_(DocumentMappingType.search().filter(product=p.slug).count(), 0)
        doc = DocumentFactory()
        RevisionFactory(document=doc, is_approved=True)
        self.refresh()
        eq_(DocumentMappingType.search().filter(product=p.slug).count(), 0)
        doc.products.add(p)
        self.refresh()
        eq_(DocumentMappingType.search().filter(product=p.slug).count(), 1)
        doc.products.remove(p)
        self.refresh()

        # Make sure the document itself is still there and that we didn't
        # accidentally delete it through screwed up signal handling:
        eq_(DocumentMappingType.search().filter().count(), 1)

        eq_(DocumentMappingType.search().filter(product=p.slug).count(), 0)

    def test_wiki_no_revisions(self):
        """Don't index documents without approved revisions"""
        # Create a document with no revisions and make sure the
        # document is not in the index.
        doc = DocumentFactory()
        self.refresh()
        eq_(DocumentMappingType.search().count(), 0)
        # Create a revision that's not approved and make sure the
        # document is still not in the index.
        RevisionFactory(document=doc, is_approved=False)
        self.refresh()
        eq_(DocumentMappingType.search().count(), 0)

    def test_wiki_redirects(self):
        """Make sure we don't index redirects"""
        # First create a revision that doesn't have a redirect and
        # make sure it's in the index.
        doc = DocumentFactory(title='wool hats')
        RevisionFactory(document=doc, is_approved=True)
        self.refresh()
        eq_(DocumentMappingType.search().query(document_title__match='wool').count(), 1)

        # Now create a revision that is a redirect and make sure the
        # document is removed from the index.
        RedirectRevisionFactory(document=doc)
        self.refresh()
        eq_(DocumentMappingType.search().query(document_title__match='wool').count(), 0)

    def test_wiki_keywords(self):
        """Make sure updating keywords updates the index."""
        # Create a document with a revision with no keywords. It
        # shouldn't show up with a document_keywords term query for
        # 'wool' since it has no keywords.
        doc = DocumentFactory(title='wool hats')
        RevisionFactory(document=doc, is_approved=True)
        self.refresh()
        eq_(DocumentMappingType.search().query(
            document_keywords='wool').count(), 0)

        RevisionFactory(document=doc, is_approved=True, keywords='wool')
        self.refresh()

        eq_(DocumentMappingType.search().query(document_keywords='wool').count(), 1)

    def test_recent_helpful_votes(self):
        """Recent helpful votes are indexed properly."""
        # Create a document and verify it doesn't show up in a
        # query for recent_helpful_votes__gt=0.
        r = RevisionFactory(is_approved=True)
        self.refresh()
        eq_(DocumentMappingType.search().filter(
            document_recent_helpful_votes__gt=0).count(), 0)

        # Add an unhelpful vote, it still shouldn't show up.
        HelpfulVoteFactory(revision=r, helpful=False)
        r.document.save()  # Votes don't trigger a reindex.
        self.refresh()
        eq_(DocumentMappingType.search().filter(
            document_recent_helpful_votes__gt=0).count(), 0)

        # Add an helpful vote created 31 days ago, it still shouldn't show up.
        created = datetime.now() - timedelta(days=31)
        HelpfulVoteFactory(revision=r, helpful=True, created=created)
        r.document.save()  # Votes don't trigger a reindex.
        self.refresh()
        eq_(DocumentMappingType.search().filter(
            document_recent_helpful_votes__gt=0).count(), 0)

        # Add an helpful vote created 29 days ago, it should show up now.
        created = datetime.now() - timedelta(days=29)
        HelpfulVoteFactory(revision=r, helpful=True, created=created)
        r.document.save()  # Votes don't trigger a reindex.
        self.refresh()
        eq_(DocumentMappingType.search().filter(
            document_recent_helpful_votes__gt=0).count(), 1)


class RevisionMetricsTests(ElasticTestCase):
    def test_add_and_delete(self):
        """Adding a revision should add it to the index.

        Deleting should delete it.
        """
        r = RevisionFactory()
        self.refresh()
        eq_(RevisionMetricsMappingType.search().count(), 1)

        r.delete()
        self.refresh()
        eq_(RevisionMetricsMappingType.search().count(), 0)

    def test_data_in_index(self):
        """Verify the data we are indexing."""
        p = ProductFactory()
        base_doc = DocumentFactory(locale='en-US', products=[p])
        d = DocumentFactory(locale='es', parent=base_doc)
        r = RevisionFactory(document=d, is_approved=True)

        self.refresh()

        eq_(RevisionMetricsMappingType.search().count(), 1)
        data = RevisionMetricsMappingType.search()[0]
        eq_(data['is_approved'], r.is_approved)
        eq_(data['locale'], d.locale)
        eq_(data['product'], [p.slug])
        eq_(data['creator_id'], r.creator_id)
