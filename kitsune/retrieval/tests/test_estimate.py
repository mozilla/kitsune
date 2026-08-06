from io import StringIO
from unittest import mock

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, override_settings

from kitsune.retrieval.chunking import chunk, count_tokens
from kitsune.retrieval.estimate import estimate_ingestion
from kitsune.wiki.tests import ApprovedRevisionFactory, DocumentFactory


def _document(number=0):
    document = DocumentFactory(title=f"Guide {number}", slug=f"guide-{number}")
    ApprovedRevisionFactory(
        document=document,
        content="How to install and configure the browser.",
    )
    document.refresh_from_db()
    return document


class IngestionEstimateTests(TestCase):
    def test_measures_chunker_output_without_calling_the_provider(self):
        document = _document()
        expected = chunk("kb", document.html, title=document.title)

        with mock.patch("kitsune.retrieval.embeddings.get_embeddings") as embed:
            estimate = estimate_ingestion()

        self.assertEqual(estimate.documents, 1)
        self.assertEqual(estimate.chunks, len(expected))
        self.assertEqual(estimate.tokens, sum(count_tokens(item.text) for item in expected))
        self.assertEqual(estimate.characters, sum(len(item.text) for item in expected))
        embed.assert_not_called()

    @override_settings(
        RETRIEVAL_BULK_MAX_DOCUMENTS=2,
        RETRIEVAL_BULK_MAX_EMBEDDING_INPUTS=500,
    )
    def test_predicts_cross_document_batching(self):
        for number in range(4):
            _document(number)

        estimate = estimate_ingestion()

        self.assertEqual(estimate.provider_requests_per_document, 4)
        self.assertEqual(estimate.provider_requests_batched, 2)
        self.assertEqual(estimate.request_multiplier, 2.0)

    @override_settings(
        RETRIEVAL_BULK_MAX_DOCUMENTS=50,
        RETRIEVAL_BULK_MAX_EMBEDDING_INPUTS=500,
    )
    def test_prediction_respects_the_provider_request_token_limit(self):
        for number in range(11):
            _document(number)

        with mock.patch("kitsune.retrieval.estimate.count_tokens", return_value=2_000):
            estimate = estimate_ingestion()

        self.assertEqual(estimate.provider_requests_per_document, 11)
        self.assertEqual(estimate.provider_requests_batched, 2)

    def test_command_reports_the_estimate_without_article_text(self):
        document = _document()
        output = StringIO()

        call_command("estimate_ingestion", stdout=output)

        rendered = output.getvalue()
        self.assertIn("Eligible documents", rendered)
        self.assertIn("per-document", rendered)
        self.assertIn("batched", rendered)
        self.assertNotIn(document.title, rendered)

    def test_command_rejects_chunks_that_the_provider_would_reject(self):
        _document()

        with (
            mock.patch("kitsune.retrieval.estimate.max_input_tokens", return_value=1),
            self.assertRaises(CommandError),
        ):
            call_command("estimate_ingestion", stdout=StringIO())
