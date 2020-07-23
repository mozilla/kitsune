from django.core.management import call_command

from unittest import mock

from kitsune.products.tests import ProductFactory
from kitsune.search import es_utils
from kitsune.search.tests import ElasticTestCase
from kitsune.search.utils import FakeLogger
from kitsune.wiki.tests import DocumentFactory, RevisionFactory


class ESCommandTests(ElasticTestCase):
    @mock.patch.object(FakeLogger, "_out")
    def test_search(self, _out):
        """Test that es_search command doesn't fail"""
        call_command("essearch", "cupcakes")

        p = ProductFactory(title="firefox", slug="desktop")
        doc = DocumentFactory(title="cupcakes rock", locale="en-US", category=10, products=[p])
        RevisionFactory(document=doc, is_approved=True)

        self.refresh()

        call_command("essearch", "cupcakes")

    @mock.patch.object(FakeLogger, "_out")
    def test_reindex(self, _out):
        p = ProductFactory(title="firefox", slug="desktop")
        doc = DocumentFactory(title="cupcakes rock", locale="en-US", category=10, products=[p])
        RevisionFactory(document=doc, is_approved=True)

        self.refresh()

        call_command("esreindex")
        call_command("esreindex", "--percent=50")
        call_command("esreindex", "--seconds-ago=60")
        call_command("esreindex", "--criticalmass")
        call_command("esreindex", "--mapping_types=wiki_documents")
        call_command("esreindex", "--delete")

    @mock.patch.object(FakeLogger, "_out")
    def test_status(self, _out):
        p = ProductFactory(title="firefox", slug="desktop")
        doc = DocumentFactory(title="cupcakes rock", locale="en-US", category=10, products=[p])
        RevisionFactory(document=doc, is_approved=True)

        self.refresh()

        call_command("esstatus")

    @mock.patch.object(FakeLogger, "_out")
    def test_delete(self, _out):
        # Note: The read indexes and the write indexes are the same in
        # the tests, so we only have to do this once.
        indexes = es_utils.all_read_indexes()
        indexes.append("cupcakerainbow_index")
        for index in indexes:
            call_command("esdelete", index, noinput=True)
