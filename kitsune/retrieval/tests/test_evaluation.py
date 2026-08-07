import json
import tempfile
from io import StringIO
from math import log2
from pathlib import Path
from unittest import mock

from django.core.management import call_command
from django.test import SimpleTestCase, TestCase

from kitsune.products.tests import ProductFactory
from kitsune.questions.tests import AnswerFactory, QuestionFactory
from kitsune.retrieval.evaluation import (
    DERIVATION,
    GoldenPair,
    GoldenSet,
    build_golden_set,
    score_lexical_search,
)
from kitsune.wiki.tests import ApprovedRevisionFactory, DocumentFactory


def _article(title, slug, locale="en-US", parent=None):
    document = DocumentFactory(title=title, slug=slug, locale=locale, parent=parent)
    ApprovedRevisionFactory(document=document, content=f"How to {title}.")
    document.refresh_from_db()
    return document


def _solved(title, content, locale="en-US", product=None):
    question = QuestionFactory(title=title, content=title, locale=locale, product=product)
    answer = AnswerFactory(question=question, content=content)
    question.solution = answer
    question.save()
    return question


class GoldenSetDerivationTests(TestCase):
    def setUp(self):
        super().setUp()
        self.article = _article("Clear cookies", "clear-cookies")

    def test_derives_a_pair_from_an_accepted_solution(self):
        question = _solved(
            "how do I delete cookies",
            "See https://support.mozilla.org/en-US/kb/clear-cookies.",
        )

        [pair] = build_golden_set().pairs

        self.assertEqual(pair.query, question.title)
        self.assertEqual(pair.locale, "en-US")
        self.assertEqual(pair.relevant_document_ids, (self.article.id,))
        self.assertEqual(pair.question_id, question.id)

    def test_wiki_links_use_the_canonical_document_family(self):
        _article("Cookies loeschen", "cookies-loeschen", "de", parent=self.article)
        _solved("wie loesche ich cookies", "See [[Cookies loeschen]].", locale="de")

        [pair] = build_golden_set().pairs

        self.assertEqual(pair.relevant_document_ids, (self.article.id,))

    def test_rejects_external_and_product_incompatible_links(self):
        _solved(
            "external",
            "See https://example.com/en-US/kb/clear-cookies.",
        )
        _solved(
            "wrong product",
            "See /kb/clear-cookies.",
            product=ProductFactory(),
        )

        self.assertEqual(build_golden_set().pairs, ())

    def test_keeps_distinct_observations_with_the_same_query(self):
        second = _article("Clear cache", "clear-cache")
        _solved("same words", "See /kb/clear-cookies.")
        _solved("same words", "See /kb/clear-cache.")

        golden = build_golden_set()

        self.assertEqual(
            {pair.relevant_document_ids for pair in golden.pairs},
            {(self.article.id,), (second.id,)},
        )


class GoldenSetFormatTests(SimpleTestCase):
    def test_round_trips_through_json(self):
        golden = GoldenSet(
            generation="2026-08-06",
            derivation=DERIVATION,
            pairs=(GoldenPair("why is it slow", "en-US", (9, 7), 42),),
        )

        restored = GoldenSet.from_json(json.loads(golden.to_json()))

        self.assertEqual(
            restored,
            GoldenSet(
                "2026-08-06", DERIVATION, (GoldenPair("why is it slow", "en-US", (7, 9), 42),)
            ),
        )


class LexicalScoringTests(TestCase):
    def test_scores_against_the_full_ideal_ranking(self):
        golden = GoldenSet("g", DERIVATION, (GoldenPair("q", "en-US", (5, 6), 1),))
        with mock.patch("kitsune.retrieval.evaluation._ranked_document_ids", return_value=[5]):
            score = score_lexical_search(golden)

        self.assertEqual(score.recall_at_k[1], 0.5)
        self.assertAlmostEqual(score.ndcg_at_10, 1 / (1 + 1 / log2(3)))

    def test_uses_the_production_search_with_the_pairs_scope(self):
        product = ProductFactory()
        golden = GoldenSet(
            "g",
            DERIVATION,
            (GoldenPair("cookies", "de", (1,), 1, product_id=product.id),),
        )

        with mock.patch("kitsune.retrieval.evaluation.WikiSearch") as search:
            search.return_value.results = [{"id": "1"}]
            score = score_lexical_search(golden)

        self.assertEqual(
            search.call_args.kwargs, {"query": "cookies", "locale": "de", "product": product}
        )
        search.return_value.run.assert_called_once_with(slice(0, 10))
        self.assertEqual(score.recall_at_k[1], 1.0)


class BaselineCommandTests(TestCase):
    def test_writes_and_reloads_the_derived_fixture(self):
        _article("Clear cookies", "clear-cookies")
        _solved("how do I delete cookies", "See /kb/clear-cookies.")

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "golden.json"
            output = StringIO()
            call_command(
                "relevance_baseline",
                "--derive-only",
                "--write",
                str(path),
                stdout=output,
            )

            payload = json.loads(path.read_text())
            self.assertEqual(len(payload["pairs"]), 1)
            self.assertIn("user-generated", output.getvalue())

            reloaded = StringIO()
            call_command(
                "relevance_baseline",
                "--derive-only",
                "--read",
                str(path),
                stdout=reloaded,
            )
            self.assertIn("Golden set:   1 pairs", reloaded.getvalue())
