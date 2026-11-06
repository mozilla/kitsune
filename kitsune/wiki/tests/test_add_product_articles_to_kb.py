from io import StringIO
from unittest.mock import call, patch

from django.core.management import call_command
from django.core.management.base import CommandError
from parameterized import parameterized

from kitsune.products.tests import ProductFactory
from kitsune.sumo.tests import TestCase
from kitsune.wiki.config import DEFAULT_AUDIENCE_SLUG
from kitsune.wiki.models import DocumentAudience
from kitsune.wiki.tests import AudienceFactory, DocumentFactory

COMMAND = "add_product_articles_to_kb"


def _assignments():
    return set(DocumentAudience.objects.values_list("document_id", "audience_id"))


class AddProductArticlesToKBTests(TestCase):
    def setUp(self):
        self.product = ProductFactory(slug="test-product")
        self.kb = AudienceFactory(slug="test-kb")

    @patch("kitsune.wiki.tasks.render_document_cascade")
    def test_adds_the_kb_to_the_products_originals(self, mock_task):
        fresh = DocumentFactory(products=[self.product])
        DocumentFactory(products=[self.product], audiences=[self.kb, AudienceFactory()])
        translation = DocumentFactory(parent=fresh, locale="de", products=[self.product])
        DocumentFactory(products=[ProductFactory(slug="other-product")])
        before = _assignments()
        out = StringIO()

        with self.captureOnCommitCallbacks(execute=True):
            call_command(COMMAND, "test-product", "test-kb", stdout=out)

        self.assertEqual(_assignments(), before | {(fresh.id, self.kb.id)})
        self.assertEqual(out.getvalue().strip(), "Articles added to test-kb: 1")
        self.assertCountEqual(
            mock_task.delay.call_args_list, [call(fresh.id), call(translation.id)]
        )

    @parameterized.expand(
        [
            ("unknown_product", "no-such-product", "test-kb"),
            ("unknown_kb", "test-product", "no-such-kb"),
            ("default_kb", "test-product", DEFAULT_AUDIENCE_SLUG),
        ]
    )
    def test_rejects_unusable_slugs(self, _name, product_slug, kb_slug):
        DocumentFactory(products=[self.product])
        before = _assignments()
        offending = kb_slug if product_slug == "test-product" else product_slug

        with self.assertRaisesRegex(CommandError, offending):
            call_command(COMMAND, product_slug, kb_slug)

        self.assertEqual(_assignments(), before)
