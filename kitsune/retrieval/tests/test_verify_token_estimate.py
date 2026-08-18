from io import StringIO
from unittest import mock

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, override_settings

from kitsune.retrieval.tests.test_embeddings import _mock_vertex_client, _vertex_response
from kitsune.wiki.tests import ApprovedRevisionFactory, DocumentFactory

VERTEX_RECIPE = {
    "RETRIEVAL_EMBEDDING_BACKEND": "vertex",
    "RETRIEVAL_EMBEDDING_MODEL": "text-embedding-005",
    "RETRIEVAL_EMBEDDING_DIMENSIONS": 8,
}


def _document(locale="en-US", number=0):
    document = DocumentFactory(
        title=f"Guide {locale} {number}",
        slug=f"guide-{locale}-{number}",
        locale=locale,
    )
    ApprovedRevisionFactory(
        document=document,
        content="How to install and configure the browser.",
    )
    document.refresh_from_db()
    return document


@override_settings(**VERTEX_RECIPE)
class VerifyTokenEstimateTests(TestCase):
    def _run(self, response=None, **options):
        client, request = _mock_vertex_client()
        if response is not None:
            request.side_effect = response
        output = StringIO()
        with mock.patch("kitsune.retrieval.embeddings._vertex_client", return_value=client):
            call_command("verify_token_estimate", stdout=output, **options)
        return output.getvalue(), request

    def test_reports_each_locale_separately_so_scripts_are_not_averaged(self):
        _document(locale="en-US")
        _document(locale="ru")

        rendered, _ = self._run()

        # One row per locale is the whole point: a mixed batch hides an over- and under-count.
        self.assertIn("en-US", rendered)
        self.assertIn("ru", rendered)
        self.assertIn("total", rendered)

    def test_reports_the_provider_count_beside_the_estimate(self):
        document = _document()

        rendered, request = self._run()

        # The stub reports 7 tokens per text, so the provider column is 7 per chunk.
        [call] = request.call_args_list
        chunks = len(call.kwargs["contents"])
        self.assertIn(f"{7 * chunks:,}", rendered)
        self.assertNotIn(document.title, rendered)

    def test_reports_the_seed_it_sampled_with(self):
        _document()

        rendered, _ = self._run()

        self.assertIn("seed:", rendered)

    def test_the_same_seed_measures_the_same_sample(self):
        for number in range(6):
            _document(number=number)

        _, first = self._run(documents=2, seed=7)
        _, second = self._run(documents=2, seed=7)

        self.assertEqual(
            [call.kwargs["contents"] for call in first.call_args_list],
            [call.kwargs["contents"] for call in second.call_args_list],
        )

    def test_a_locale_sample_does_not_depend_on_the_other_locales_asked_for(self):
        for number in range(6):
            _document(locale="de", number=number)

        _, alone = self._run(documents=2, seed=7, locale=["de"])
        _, alongside = self._run(documents=2, seed=7, locale=["de", "ru"])

        self.assertEqual(
            [call.kwargs["contents"] for call in alone.call_args_list],
            [call.kwargs["contents"] for call in alongside.call_args_list],
        )

    def test_bounds_what_the_sample_costs(self):
        for number in range(4):
            _document(number=number)

        _, request = self._run(**{"max_chunks": 1})

        self.assertEqual([len(call.kwargs["contents"]) for call in request.call_args_list], [1])

    def test_an_unreported_provider_count_reads_as_unknown(self):
        _document()

        rendered, _ = self._run(
            response=lambda **kwargs: _vertex_response(kwargs["contents"], token_count=None)
        )

        self.assertIn("unknown", rendered)
        self.assertIn("n/a", rendered)

    def test_reports_nothing_rather_than_embedding_an_empty_sample(self):
        rendered, request = self._run()

        self.assertIn("nothing measured", rendered)
        request.assert_not_called()

    def test_rejects_a_non_positive_sample_size(self):
        with self.assertRaisesMessage(CommandError, "--documents"):
            call_command("verify_token_estimate", documents=0)
