from kitsune.sumo.tests import TestCase
from kitsune.sumo.urlresolvers import reverse
from kitsune.wiki.tests import ApprovedRevisionFactory, DocumentFactory


class TestDocumentListView(TestCase):
    def test_it_works(self):
        # Create two documents, one with approved content, and one without.
        doc1 = DocumentFactory()
        doc2 = ApprovedRevisionFactory().document
        url = reverse("document-list")
        res = self.client.get(url)
        # Only the document with approved content should be present.
        self.assertNotContains(res, doc1.slug)
        self.assertNotContains(res, doc1.title)
        self.assertContains(res, doc2.slug, count=1)
        self.assertContains(res, doc2.title, count=1)
