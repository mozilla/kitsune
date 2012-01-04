from wiki.tests import ESTestCase, document
from wiki.models import Document
from wiki.es_search import extract_document

import elasticutils
import uuid

from nose.tools import eq_


class TestPostUpdate(ESTestCase):
    def test_added(self):
        # Use a uuid since it's "unique" and makes sure we're not
        # accidentally picking up a Post we don't want.
        title = str(uuid.uuid4())

        doc = document(title=title)

        original_count = elasticutils.S(Document).count()

        doc.save()
        self.refresh()

        eq_(elasticutils.S(Document).count(), original_count + 1)

    def test_deleted(self):
        # Use a uuid since it's "unique" and makes sure we're not
        # accidentally picking up a Post we don't want.
        title = str(uuid.uuid4())

        original_count = elasticutils.S(Document).count()

        doc = document(title=title)
        doc.save()
        self.refresh()

        eq_(elasticutils.S(Document).count(), original_count + 1)

        doc.delete()
        self.refresh()

        eq_(elasticutils.S(Document).count(), original_count)

    def test_translations_get_parent_tags(self):
        doc1 = document(title=u'Audio too loud')
        doc1.save()
        doc1.tags.add(u'desktop')
        doc1.tags.add(u'windows')

        doc2 = document(title=u'Audio too loud bork bork',
                        parent=doc1)
        doc2.save()
        doc2.tags.add(u'badtag')

        # Verify the parent has the right tags.
        doc_dict = extract_document(doc1)
        eq_(doc_dict['tag'], [u'desktop', u'windows'])

        # Verify the translation has the parent's tags.
        doc_dict = extract_document(doc2)
        eq_(doc_dict['tag'], [u'desktop', u'windows'])
