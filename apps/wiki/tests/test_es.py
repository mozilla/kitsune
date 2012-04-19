import elasticutils
from nose.tools import eq_

from search.tests.test_es import ElasticTestCase
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
        eq_(elasticutils.S(Document).count(), 1)

        doc.delete()
        self.refresh()
        eq_(elasticutils.S(Document).count(), 0)

    def test_translations_get_parent_tags(self):
        doc1 = document(title=u'Audio too loud')
        doc1.save()
        revision(document=doc1, is_approved=True, save=True)
        doc1.tags.add(u'desktop')
        doc1.tags.add(u'windows')

        doc2 = document(title=u'Audio too loud bork bork',
                        parent=doc1)
        doc2.save()
        revision(document=doc2, is_approved=True, save=True)
        doc2.tags.add(u'badtag')

        # Verify the parent has the right tags.
        doc_dict = Document.extract_document(doc1.id)
        eq_(doc_dict['tag'], [u'desktop', u'windows'])

        # Verify the translation has the parent's tags.
        doc_dict = Document.extract_document(doc2.id)
        eq_(doc_dict['tag'], [u'desktop', u'windows'])

    def test_wiki_tags(self):
        """Make sure that adding tags to a Document causes it to
        refresh the index.

        """
        tag = u'hiphop'
        eq_(elasticutils.S(Document).filter(tag=tag).count(), 0)
        doc = document(save=True)
        revision(document=doc, is_approved=True, save=True)
        self.refresh()
        eq_(elasticutils.S(Document).filter(tag=tag).count(), 0)
        doc.tags.add(tag)
        self.refresh()
        eq_(elasticutils.S(Document).filter(tag=tag).count(), 1)
        doc.tags.remove(tag)
        self.refresh()

        # Make sure the document itself is still there and that we didn't
        # accidentally delete it through screwed up signal handling:
        eq_(elasticutils.S(Document).filter().count(), 1)

        eq_(elasticutils.S(Document).filter(tag=tag).count(), 0)

    def test_wiki_no_revisions(self):
        """Don't index documents without approved revisions"""
        # Create a document with no revisions and make sure the
        # document is not in the index.
        doc = document(save=True)
        self.refresh()
        eq_(elasticutils.S(Document).count(), 0)
        # Create a revision that's not approved and make sure the
        # document is still not in the index.
        revision(document=doc, is_approved=False, save=True)
        self.refresh()
        eq_(elasticutils.S(Document).count(), 0)

    def test_wiki_redirects(self):
        """Make sure we don't index redirects"""
        # First create a revision that doesn't have a redirect and
        # make sure it's in the index.
        doc = document(title=u'wool hats')
        doc.save()
        revision(document=doc, is_approved=True, save=True)
        self.refresh()
        eq_(elasticutils.S(Document).query('wool').count(), 1)

        # Now create a revision that is a redirect and make sure the
        # document is removed from the index.
        revision(document=doc, content=REDIRECT_CONTENT, is_approved=True,
                 save=True)
        self.refresh()
        eq_(elasticutils.S(Document).query('wool').count(), 0)
