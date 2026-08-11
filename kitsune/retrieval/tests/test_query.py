from datetime import UTC, datetime
from unittest import mock

from django.test import SimpleTestCase, override_settings
from elasticsearch.helpers import bulk

from kitsune.retrieval.fingerprints import similarity_profile_fingerprint
from kitsune.retrieval.index import VECTOR_DIMS, ChunkDocument, configured_index_meta
from kitsune.retrieval.query import (
    RRF_RANK_CONSTANT,
    SimilarityFloorUnavailable,
    _build_retriever,
    build_lexical_clauses,
    similarity_floor_for_index,
)
from kitsune.retrieval.tests import ChunkIndexTestCase
from kitsune.search.documents import QuestionDocument
from kitsune.search.es_utils import es_client


def _contains(value, expected):
    if value == expected:
        return True
    if isinstance(value, dict):
        return any(_contains(item, expected) for item in value.values())
    if isinstance(value, list):
        return any(_contains(item, expected) for item in value)
    return False


def _simple_query(clause):
    return clause.to_dict()["bool"]["must"][0]["simple_query_string"]


class LexicalClauseTests(SimpleTestCase):
    def test_builds_requested_and_fallback_clauses_for_both_sources(self):
        clauses = build_lexical_clauses(
            "firefox startup",
            locale="de",
            sources={"kb", "aaq"},
            viewer_group_ids=(9, 7),
            product_id=3,
            default_operator="OR",
            minimum_should_match="2<75%",
        )

        kb = clauses.kb_requested.to_dict()
        self.assertEqual(
            _simple_query(clauses.kb_requested),
            {
                "query": "firefox startup",
                "default_operator": "OR",
                "fields": [
                    "keywords.de^8",
                    "title.de^6",
                    "summary.de^4",
                    "content_text.de^2",
                ],
                "flags": "PHRASE",
                "minimum_should_match": "2<75%",
            },
        )
        self.assertTrue(_contains(kb, {"prefix": {"family_id": "kb:"}}))
        self.assertTrue(_contains(kb, {"terms": {"access_group_ids": [7, 9]}}))
        self.assertTrue(_contains(kb, {"term": {"product_ids": "3"}}))

        self.assertEqual(
            _simple_query(clauses.kb_english)["fields"],
            [
                "keywords.en-US^8",
                "title.en-US^6",
                "summary.en-US^4",
                "content_text.en-US^2",
            ],
        )

        aaq = clauses.aaq_requested.to_dict()
        aaq_query = aaq["bool"]["must"][0]["bool"]
        self.assertEqual(
            aaq_query["must"][0]["simple_query_string"]["fields"],
            ["question_title.de^2", "question_content.de", "answer_content.de"],
        )
        self.assertEqual(aaq_query["must_not"], [{"exists": {"field": "updated"}}])
        self.assertTrue(_contains(aaq, {"prefix": {"family_id": "aaq:"}}))
        self.assertTrue(_contains(aaq, {"term": {"question_product_id": 3}}))
        self.assertFalse(_contains(kb, {"exists": {"field": "updated"}}))

    def test_source_selection_does_not_create_unused_or_duplicate_clauses(self):
        aaq = build_lexical_clauses("firefox", locale="de", sources={"aaq"}, viewer_group_ids=())
        self.assertIsNone(aaq.kb_requested)
        self.assertIsNone(aaq.kb_english)
        self.assertIsNotNone(aaq.aaq_requested)

        kb = build_lexical_clauses("firefox", locale="en-US", sources={"kb"}, viewer_group_ids=())
        self.assertIsNotNone(kb.kb_requested)
        self.assertIsNone(kb.kb_english)
        self.assertIsNone(kb.aaq_requested)

    def test_rejects_invalid_viewer_group_ids(self):
        for group_ids in ("12", (True,), (0,), (1.5,)):
            with self.subTest(group_ids=group_ids), self.assertRaises(ValueError):
                build_lexical_clauses(
                    "firefox",
                    locale="en-US",
                    sources={"kb"},
                    viewer_group_ids=group_ids,  # type: ignore[arg-type]
                )

    def test_advanced_fields_are_rendered_for_each_source(self):
        clauses = build_lexical_clauses(
            'field:content:"startup crash" OR field:title:firefox',
            locale="en-US",
            sources={"kb", "aaq"},
            viewer_group_ids=(),
            default_operator="OR",
            minimum_should_match="2<75%",
        )

        kb = clauses.kb_requested.to_dict()
        self.assertTrue(
            _contains(
                kb,
                {
                    "simple_query_string": {
                        "query": '"startup crash"',
                        "default_operator": "OR",
                        "fields": ["content_text.en-US"],
                        "flags": "PHRASE",
                        "minimum_should_match": "2<75%",
                    }
                },
            )
        )

        aaq = clauses.aaq_requested.to_dict()
        self.assertTrue(
            _contains(
                aaq,
                {
                    "simple_query_string": {
                        "query": '"startup crash"',
                        "default_operator": "OR",
                        "fields": ["question_content.en-US", "answer_content.en-US"],
                        "flags": "PHRASE",
                        "minimum_should_match": "2<75%",
                    }
                },
            )
        )


class NativeRetrieverCompositionTests(SimpleTestCase):
    def test_separate_locale_composition_uses_collapsed_children_and_distinct_bounds(self):
        retriever = _build_retriever(
            "firefox startup",
            kb_index="retrieval-42",
            locale="de",
            sources={"kb", "aaq"},
            viewer_group_ids=(9, 7),
            product_id=3,
            query_vector=[1.0, 0.0],
            similarity_floor=0.75,
            semantic_k=40,
            num_candidates=90,
            rank_window_size=60,
            locale_composition="separate",
            default_operator="OR",
            minimum_should_match="2<75%",
        )

        rrf = retriever["rrf"]
        self.assertEqual(rrf["rank_constant"], RRF_RANK_CONSTANT)
        self.assertEqual(rrf["rank_window_size"], 60)
        self.assertEqual(len(rrf["retrievers"]), 3)
        self.assertTrue(
            all(
                child["standard"]["collapse"] == {"field": "family_id"}
                for child in rrf["retrievers"]
            )
        )

        semantic = rrf["retrievers"][-1]["standard"]["query"]["knn"]
        self.assertEqual(
            {key: semantic[key] for key in ("k", "num_candidates", "similarity")},
            {"k": 40, "num_candidates": 90, "similarity": 0.75},
        )
        self.assertTrue(_contains(semantic, {"term": {"_index": "retrieval-42"}}))
        self.assertTrue(_contains(semantic, {"terms": {"locale": ["de", "en-US"]}}))
        self.assertTrue(_contains(semantic, {"terms": {"access_group_ids": [7, 9]}}))
        self.assertTrue(_contains(semantic, {"term": {"product_ids": "3"}}))

    def test_aaq_only_ignores_the_vector_and_avoids_unnecessary_rrf(self):
        retriever = _build_retriever(
            "firefox",
            kb_index=None,
            locale="de",
            sources={"aaq"},
            viewer_group_ids=(),
            product_id=None,
            query_vector=[1.0, 0.0],
            similarity_floor=None,
            semantic_k=10,
            num_candidates=20,
            rank_window_size=30,
            locale_composition="separate",
        )

        self.assertIn("standard", retriever)
        self.assertNotIn("rrf", retriever)
        self.assertNotIn("knn", retriever["standard"]["query"])

        locale_fallback = _build_retriever(
            "firefox",
            kb_index="retrieval-42",
            locale="de",
            sources={"kb"},
            viewer_group_ids=(),
            product_id=None,
            query_vector=None,
            similarity_floor=None,
            semantic_k=10,
            num_candidates=20,
            rank_window_size=30,
            locale_composition="separate",
        )
        self.assertEqual(len(locale_fallback["rrf"]["retrievers"]), 2)
        self.assertEqual(locale_fallback["rrf"]["rank_constant"], RRF_RANK_CONSTANT)

    def test_floor_is_bound_to_the_exact_index_profile(self):
        meta = configured_index_meta()
        _, fingerprint = similarity_profile_fingerprint(meta)
        floors = {fingerprint: 0.81, "a" * 64: 0.5}

        with (
            override_settings(RETRIEVAL_KNN_SIMILARITY_FLOORS=floors),
            mock.patch("kitsune.retrieval.query.read_index_meta", return_value=meta),
        ):
            self.assertEqual(similarity_floor_for_index("retrieval-42"), 0.81)

        with (
            override_settings(RETRIEVAL_KNN_SIMILARITY_FLOORS={"a" * 64: 0.5}),
            mock.patch("kitsune.retrieval.query.read_index_meta", return_value=meta),
            self.assertRaises(SimilarityFloorUnavailable),
        ):
            similarity_floor_for_index("retrieval-42")

        with self.assertRaises(SimilarityFloorUnavailable):
            _build_retriever(
                "firefox",
                kb_index="retrieval-42",
                locale="en-US",
                sources={"kb"},
                viewer_group_ids=(),
                product_id=None,
                query_vector=[1.0, 0.0],
                similarity_floor=1.01,
                semantic_k=10,
                num_candidates=20,
                rank_window_size=20,
                locale_composition="combined",
            )


class NativeRetrieverElasticsearchTests(ChunkIndexTestCase):
    def test_native_rrf_collapses_families_and_applies_the_semantic_floor(self):
        client = es_client().options(request_timeout=30)
        now = datetime.now(UTC)
        exact = [1.0, *([0.0] * (VECTOR_DIMS - 1))]
        distant = [0.0, 1.0, *([0.0] * (VECTOR_DIMS - 2))]
        actions = []
        for position in range(10):
            actions.append(
                {
                    "_index": ChunkDocument.Index.write_alias,
                    "_id": f"long-{position}",
                    "_source": {
                        "kind": "chunk",
                        "content_type": "kb",
                        "object_id": "1",
                        "family_id": "kb:1",
                        "locale": "en-US",
                        "position": position,
                        "visibility": "public",
                        "access_group_ids": [],
                        "product_ids": ["3"],
                        "title": {"en-US": "firefox startup crash"},
                        "content_text": {"en-US": f"long article passage {position}"},
                        "content_vector": distant,
                        "updated": now,
                    },
                }
            )
        actions.extend(
            [
                {
                    "_index": ChunkDocument.Index.write_alias,
                    "_id": "short-0",
                    "_source": {
                        "kind": "chunk",
                        "content_type": "kb",
                        "object_id": "2",
                        "family_id": "kb:2",
                        "locale": "en-US",
                        "position": 0,
                        "visibility": "public",
                        "access_group_ids": [],
                        "product_ids": ["3"],
                        "title": {"en-US": "firefox startup crash"},
                        "content_text": {"en-US": "short exact semantic passage"},
                        "content_vector": exact,
                        "updated": now,
                    },
                },
                {
                    "_index": QuestionDocument.Index.write_alias,
                    "_id": "question-3",
                    "_source": {
                        "question_id": "3",
                        "family_id": "aaq:3",
                        "locale": "en-US",
                        "question_title": {"en-US": "firefox startup crash"},
                        "question_content": {"en-US": "community troubleshooting"},
                        "question_created": now,
                        "question_has_answers": True,
                        "question_is_archived": False,
                        "question_product_id": 3,
                    },
                },
            ]
        )
        bulk(client, actions, refresh=True)

        retriever = _build_retriever(
            "firefox startup crash",
            kb_index=ChunkDocument.Index.read_alias,
            locale="en-US",
            sources={"kb", "aaq"},
            viewer_group_ids=(),
            product_id=3,
            query_vector=exact,
            similarity_floor=0.99,
            semantic_k=12,
            num_candidates=20,
            rank_window_size=20,
            locale_composition="combined",
        )
        indices = [ChunkDocument.Index.read_alias, QuestionDocument.Index.read_alias]

        mixed = client.search(
            index=indices,
            retriever=retriever,
            collapse={"field": "family_id"},
            size=10,
            allow_partial_search_results=False,
        )
        self.assertEqual(
            {hit["_source"]["family_id"] for hit in mixed["hits"]["hits"]},
            {"kb:1", "kb:2", "aaq:3"},
        )

        lexical, semantic = retriever["rrf"]["retrievers"]
        lexical_hits = client.search(
            index=ChunkDocument.Index.read_alias,
            retriever=lexical,
            size=2,
            allow_partial_search_results=False,
        )
        self.assertEqual(
            {hit["_source"]["family_id"] for hit in lexical_hits["hits"]["hits"]},
            {"kb:1", "kb:2"},
        )

        aaq_hits = client.search(
            index=QuestionDocument.Index.read_alias,
            retriever=lexical,
            size=1,
            allow_partial_search_results=False,
        )
        [aaq_hit] = aaq_hits["hits"]["hits"]
        self.assertGreater(aaq_hit["_score"], 0)

        semantic_hits = client.search(
            index=indices,
            retriever=semantic,
            size=10,
            allow_partial_search_results=False,
        )
        self.assertEqual(
            [hit["_source"]["family_id"] for hit in semantic_hits["hits"]["hits"]],
            ["kb:2"],
        )
