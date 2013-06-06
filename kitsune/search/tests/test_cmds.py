from django.core.management import call_command

import mock

from kitsune.products.tests import product
from kitsune.search import es_utils
from kitsune.search.tests import ElasticTestCase
from kitsune.search.utils import FakeLogger
from kitsune.wiki.tests import document, revision


class ESCommandTests(ElasticTestCase):
    @mock.patch.object(FakeLogger, '_out')
    def test_search(self, _out):
        """Test that es_search command doesn't fail"""
        call_command('essearch', 'cupcakes')

        doc = document(title=u'cupcakes rock', locale=u'en-US', category=10,
                       save=True)
        doc.products.add(product(title=u'firefox', slug=u'desktop', save=True))
        revision(document=doc, is_approved=True, save=True)

        self.refresh()

        call_command('essearch', 'cupcakes')

    @mock.patch.object(FakeLogger, '_out')
    def test_reindex(self, _out):
        doc = document(title=u'cupcakes rock', locale=u'en-US', category=10,
                       save=True)
        doc.products.add(product(title=u'firefox', slug=u'desktop', save=True))
        revision(document=doc, is_approved=True, save=True)

        self.refresh()

        call_command('esreindex')
        call_command('esreindex', '--percent=50')
        call_command('esreindex', '--criticalmass')
        call_command('esreindex', '--mapping_types=wiki_documents')
        call_command('esreindex', '--delete')

    @mock.patch.object(FakeLogger, '_out')
    def test_status(self, _out):
        doc = document(title=u'cupcakes rock', locale=u'en-US', category=10,
                       save=True)
        doc.products.add(product(title=u'firefox', slug=u'desktop', save=True))
        revision(document=doc, is_approved=True, save=True)

        self.refresh()

        call_command('esstatus')

    @mock.patch.object(FakeLogger, '_out')
    def test_delete(self, _out):
        # Note: READ_INDEX == WRITE_INDEX in the tests, so we only
        # have to do one.
        for index in [es_utils.READ_INDEX,
                      'cupcakerainbow_index']:
            call_command('esdelete', index, noinput=True)
