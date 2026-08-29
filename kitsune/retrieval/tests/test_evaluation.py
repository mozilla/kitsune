import json
from dataclasses import replace
from math import log2
from unittest import mock

from django.test import SimpleTestCase, TestCase

from kitsune.products.tests import ProductFactory
from kitsune.questions.tests import AnswerFactory, QuestionFactory
from kitsune.retrieval.embeddings import EmbeddingRecipe
from kitsune.retrieval.evaluation import (
    DERIVATION,
    EvaluationArtifact,
    EvaluationConfig,
    EvaluationQuery,
    InvalidEvaluationArtifact,
    InvalidEvaluationResult,
    _current_lexical_ranking,
    _run_retrieval,
    build_positive_artifact,
    evaluate_artifacts,
    freeze_no_answer_artifact,
    score_no_answer,
    score_rankings,
    validate_split_coverage,
)
from kitsune.retrieval.query import RetrievalResult
from kitsune.wiki.tests import ApprovedRevisionFactory, DocumentFactory


def _article(title, slug, locale="en-US", parent=None, **kwargs):
    document = DocumentFactory(title=title, slug=slug, locale=locale, parent=parent, **kwargs)
    ApprovedRevisionFactory(document=document, content=f"How to {title}.")
    document.refresh_from_db()
    return document


def _solved(title, content, locale="en-US", **kwargs):
    question = QuestionFactory(title=title, content=title, locale=locale, **kwargs)
    answer = AnswerFactory(question=question, content=content)
    question.solution = answer
    question.save()
    return question


def _query(query_id, relevant=()):
    return EvaluationQuery(
        query_id=query_id,
        query="firefox problem",
        locale="en-US",
        relevant_family_ids=tuple(relevant),
        source_family_id=query_id if relevant else None,
        product_id=None,
        split="tuning",
    )


class EvaluationArtifactTests(TestCase):
    def test_positive_artifact_uses_namespaced_families_and_frozen_metadata(self):
        original = _article("Clear cookies", "clear-cookies")
        _article("Cookies loeschen", "cookies-loeschen", "de", parent=original)
        question = _solved("wie loesche ich cookies", "See [[Cookies loeschen]].", locale="de")

        artifact = build_positive_artifact(
            environment="stage",
            read_generation="sumo_chunkdocument_20260813010101",
        )
        restored = EvaluationArtifact.from_json(json.loads(artifact.to_json()))

        self.assertEqual(restored, artifact)
        self.assertEqual(artifact.derivation, DERIVATION)
        self.assertEqual(artifact.environment, "stage")
        self.assertEqual(artifact.read_generation, "sumo_chunkdocument_20260813010101")
        self.assertEqual(artifact.queries[0].query_id, f"aaq:{question.id}")
        self.assertEqual(artifact.queries[0].relevant_family_ids, (f"kb:{original.id}",))
        self.assertIn(artifact.queries[0].split, ("tuning", "holdout"))

    def test_no_answer_artifact_rejects_changed_content(self):
        artifact = freeze_no_answer_artifact(
            [{"query": "unrelated words", "locale": "en-US"}],
            environment="production",
            read_generation="sumo_chunkdocument_20260813010101",
        )
        payload = json.loads(artifact.to_json())
        payload["queries"][0]["query"] = "changed words"

        with self.assertRaisesMessage(InvalidEvaluationArtifact, "digest"):
            EvaluationArtifact.from_json(payload)

        payload["digest"] = 7
        with self.assertRaises(InvalidEvaluationArtifact):
            EvaluationArtifact.from_json(payload)

    def test_an_artifact_must_support_both_evaluation_splits(self):
        artifact = freeze_no_answer_artifact(
            [{"query": "unrelated words", "locale": "en-US"}],
            environment="production",
            read_generation="sumo_chunkdocument_20260813010101",
        )

        with self.assertRaisesMessage(InvalidEvaluationArtifact, "tuning and one holdout"):
            validate_split_coverage(artifact)


class EvaluationMetricTests(SimpleTestCase):
    def test_scores_multilabel_relevance_and_misses(self):
        queries = (_query("aaq:1", ("kb:5", "kb:6")), _query("aaq:2", ("kb:9",)))

        score = score_rankings(queries, {"aaq:1": ["kb:5"], "aaq:2": []})

        self.assertEqual(score.recall_at_k[1], 0.25)
        self.assertAlmostEqual(score.ndcg_at_10, 1 / (1 + 1 / log2(3)) / 2)
        self.assertEqual(score.empty_results, 1)
        self.assertEqual(score.missed_query_ids, ("aaq:2",))

        with self.assertRaisesMessage(ValueError, "at least one label"):
            score_rankings((_query("no-answer:1"),), {"no-answer:1": []})

    def test_keeps_no_answer_semantic_and_hybrid_returns_separate(self):
        queries = (_query("no-answer:1"), _query("no-answer:2"))

        score = score_no_answer(
            queries,
            {"no-answer:1": ["kb:1"], "no-answer:2": []},
            {"no-answer:1": ["kb:1"], "no-answer:2": ["aaq:7"]},
        )

        self.assertEqual(score["semantic_kb_returns"], 1)
        self.assertEqual(score["full_hybrid_returns"], 2)
        self.assertEqual(score["semantic_returned_query_ids"], ["no-answer:1"])

    def test_configuration_records_the_fixed_rrf_policy(self):
        config = EvaluationConfig(
            similarity_floor=0.75,
            similarity_profile="a" * 64,
            semantic_k=100,
            num_candidates=200,
            rank_window_size=100,
            default_operator="OR",
            minimum_should_match="2<-1",
            locale_composition="combined",
        )

        self.assertEqual(config.to_payload()["rank_constant"], 60)
        self.assertEqual(config.to_payload()["minimum_should_match"], "2<-1")

        with self.assertRaisesMessage(ValueError, "applies only to OR"):
            replace(config, default_operator="AND")


class EvaluationRunTests(TestCase):
    def test_legacy_search_names_a_malformed_index_result(self):
        with (
            mock.patch("kitsune.retrieval.evaluation.WikiSearch") as wiki_search,
            self.assertRaisesMessage(
                InvalidEvaluationResult,
                "repair or reindex WikiDocument before evaluation",
            ),
        ):
            wiki_search.return_value.run.side_effect = KeyError("en-US")
            _current_lexical_ranking(_query("aaq:1"), None)

    def test_new_modes_cross_the_database_authorization_boundary(self):
        config = EvaluationConfig(
            similarity_floor=0.75,
            similarity_profile="a" * 64,
            semantic_k=10,
            num_candidates=20,
            rank_window_size=20,
            default_operator="AND",
            minimum_should_match=None,
            locale_composition="combined",
        )
        indexed = mock.sentinel.indexed
        authorized = mock.sentinel.authorized

        with (
            mock.patch(
                "kitsune.retrieval.evaluation._retrieve_unvalidated",
                return_value=indexed,
            ),
            mock.patch(
                "kitsune.retrieval.evaluation.authorize_candidates",
                return_value=authorized,
            ) as authorize,
        ):
            result = _run_retrieval(
                _query("aaq:1", ("kb:1",)),
                vector=None,
                config=config,
                read_generation="retrieval-1",
                sources={"kb"},
            )

        self.assertIs(result, authorized)
        authorize.assert_called_once_with(
            indexed,
            viewer_access=mock.ANY,
            locale="en-US",
            product_id=None,
            page_size=10,
        )

    def test_runs_fixed_modes_and_excludes_the_source_question(self):
        article = _article("Clear cookies", "clear-cookies")
        question = _solved("delete cookies", "See /kb/clear-cookies.")
        generation = "sumo_chunkdocument_20260813010101"
        config = EvaluationConfig(
            similarity_floor=0.75,
            similarity_profile="a" * 64,
            semantic_k=10,
            num_candidates=20,
            rank_window_size=20,
            default_operator="OR",
            minimum_should_match="2<75%",
            locale_composition="combined",
        )
        recipe = EmbeddingRecipe("fake", "", 2, "doc", "query", "none")

        def run(evaluation_query, *, sources, excluded_family_ids=(), **kwargs):
            if "aaq" in sources and evaluation_query.source_family_id:
                self.assertEqual(excluded_family_ids, (f"aaq:{question.id}",))
            family = (
                evaluation_query.relevant_family_ids[0]
                if evaluation_query.relevant_family_ids
                else "kb:99"
            )
            candidate = mock.Mock(family_id=family)
            return RetrievalResult(
                (candidate,),
                1,
                False,
                "hybrid",
                False,
                0,
                1,
                ((family, 2),),
            )

        with (
            mock.patch("kitsune.retrieval.evaluation._split_for", return_value="tuning"),
            mock.patch("kitsune.retrieval.evaluation.get_embeddings", return_value=[[1, 0]] * 2),
            mock.patch("kitsune.retrieval.evaluation._run_retrieval", side_effect=run),
            mock.patch(
                "kitsune.retrieval.evaluation._current_lexical_ranking",
                return_value=[f"kb:{article.id}"],
            ),
        ):
            positive = build_positive_artifact(environment="stage", read_generation=generation)
            no_answer = freeze_no_answer_artifact(
                [{"query": "no useful answer", "locale": "en-US"}],
                environment="stage",
                read_generation=generation,
            )
            report = evaluate_artifacts(
                positive,
                no_answer,
                environment="stage",
                read_generation=generation,
                recipe=recipe,
                config=config,
                split="tuning",
            )

        self.assertEqual(report["positive"]["rrf"]["recall_at_k"]["1"], 1.0)
        self.assertEqual(report["no_answer"]["semantic_kb_returns"], 1)
        self.assertFalse(report["mixed"]["unlabelled_aaq_treated_as_irrelevant"])

    def test_evaluation_rejects_a_product_removed_after_freezing(self):
        product = ProductFactory()
        _article("Clear cookies", "clear-cookies", products=[product])
        _solved(
            "delete cookies",
            "See /kb/clear-cookies.",
            product=product,
        )
        generation = "sumo_chunkdocument_20260813010101"
        config = EvaluationConfig(
            similarity_floor=0.75,
            similarity_profile="a" * 64,
            semantic_k=10,
            num_candidates=20,
            rank_window_size=20,
            default_operator="AND",
            minimum_should_match=None,
            locale_composition="combined",
        )

        with mock.patch("kitsune.retrieval.evaluation._split_for", return_value="tuning"):
            positive = build_positive_artifact(environment="stage", read_generation=generation)
            no_answer = freeze_no_answer_artifact(
                [{"query": "no useful answer", "locale": "en-US"}],
                environment="stage",
                read_generation=generation,
            )
            with (
                mock.patch(
                    "kitsune.retrieval.evaluation.Product.objects.in_bulk", return_value={}
                ),
                self.assertRaisesMessage(ValueError, "product that no longer exists"),
            ):
                evaluate_artifacts(
                    positive,
                    no_answer,
                    environment="stage",
                    read_generation=generation,
                    recipe=EmbeddingRecipe("fake", "", 2, "doc", "query", "none"),
                    config=config,
                    split="tuning",
                )
