from datetime import UTC, datetime
from unittest import mock

from django.test import SimpleTestCase, override_settings
from elasticsearch.helpers import bulk

from kitsune.retrieval.fingerprints import similarity_profile_fingerprint
from kitsune.retrieval.index import VECTOR_DIMS, ChunkDocument, configured_index_meta
from kitsune.retrieval.query import (
    RRF_RANK_CONSTANT,
    InvalidRetrievalResponse,
    LegacyQuestion,
    RetrievalPassage,
    SimilarityFloorUnavailable,
    _build_retriever,
    _decode_response,
    _retrieve_unvalidated,
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

    def test_privileged_viewer_can_retrieve_public_and_restricted_kb_content(self):
        clauses = build_lexical_clauses(
            "firefox",
            locale="en-US",
            sources={"kb"},
            viewer_group_ids=(),
            privileged=True,
        )

        self.assertTrue(
            _contains(
                clauses.kb_requested.to_dict(),
                {"terms": {"visibility": ["public", "group_restricted"]}},
            )
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
    def test_evaluation_can_exclude_its_source_thread_and_run_semantic_only(self):
        mixed = _build_retriever(
            "firefox",
            kb_index="retrieval-42",
            locale="en-US",
            sources={"kb", "aaq"},
            viewer_group_ids=(),
            product_id=None,
            query_vector=[1.0, 0.0],
            similarity_floor=0.75,
            semantic_k=10,
            num_candidates=20,
            rank_window_size=20,
            locale_composition="combined",
            excluded_family_ids={"aaq:7"},
        )
        semantic = _build_retriever(
            "firefox",
            kb_index="retrieval-42",
            locale="en-US",
            sources={"kb"},
            viewer_group_ids=(),
            product_id=None,
            query_vector=[1.0, 0.0],
            similarity_floor=0.75,
            semantic_k=10,
            num_candidates=20,
            rank_window_size=20,
            locale_composition="combined",
            include_lexical=False,
        )

        self.assertTrue(_contains(mixed, {"terms": {"family_id": ["aaq:7"]}}))
        self.assertEqual(set(semantic["standard"]["query"]), {"knn"})

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


class BoundedRetrievalTests(SimpleTestCase):
    def test_executes_and_decodes_bounded_mixed_results(self):
        response = {
            "took": 7,
            "timed_out": False,
            "_shards": {"total": 2, "successful": 1, "skipped": 0, "failed": 1},
            "hits": {
                "hits": [
                    {
                        "_score": 0.03,
                        "matched_queries": ["lexical:kb:en-US", "semantic:kb"],
                        "_source": {
                            "kind": "chunk",
                            "content_type": "kb",
                            "object_id": "41",
                            "family_id": "kb:41",
                            "locale": "en-US",
                            "position": 2,
                            "heading_path": "Firefox > Startup",
                            "scope": {"version": 1, "clauses": [["win", "mac"]]},
                            "content_text": {"en-US": "Firefox starts in safe mode."},
                            "product_ids": ["1"],
                            "topic_ids": ["7"],
                            "category": "10",
                        },
                        "highlight": {
                            "content_text.en-US": ["<strong>Firefox</strong> starts."],
                            "summary.en-US": ["Fix <strong>Firefox</strong> startup."],
                        },
                    },
                    {
                        "_score": 0.02,
                        "_source": {
                            "question_id": "9",
                            "family_id": "aaq:9",
                            "locale": "en-US",
                            "question_title": {"en-US": "Firefox will not start"},
                            "question_content": {"en-US": "How can I open Firefox?"},
                            "answer_content": {"en-US": ["Try safe mode."]},
                            "question_updated": "2026-08-11T10:00:00+00:00",
                            "question_has_solution": True,
                            "question_num_votes": 3,
                        },
                        "highlight": {
                            "question_content.en-US": ["How can I open <strong>Firefox</strong>?"],
                        },
                    },
                    {"extra_collapsed_family": True},
                ]
            },
            "aggregations": {
                "families": {"value": 3},
                "family_distribution": {
                    "buckets": [
                        {"key": "kb:41", "doc_count": 4},
                        {"key": "aaq:9", "doc_count": 1},
                    ]
                },
            },
        }
        client = mock.Mock()
        client.search.return_value = response

        with mock.patch("kitsune.retrieval.query.es_client", return_value=client):
            result = _retrieve_unvalidated(
                "firefox startup",
                kb_index="retrieval-42",
                locale="en-US",
                sources={"kb", "aaq"},
                viewer_group_ids=(),
                product_id=None,
                query_vector=[1.0, 0.0],
                similarity_floor=0.75,
                semantic_k=10,
                num_candidates=20,
                rank_window_size=20,
                locale_composition="combined",
                page_size=2,
                offset=4,
                max_offset=10,
                family_distribution_size=10,
            )

        self.assertEqual([candidate.rank for candidate in result.candidates], [5, 6])
        self.assertEqual(result.approximate_total, 3)
        self.assertEqual(result.family_counts, (("kb:41", 4), ("aaq:9", 1)))
        self.assertTrue(result.has_more)
        self.assertTrue(result.degraded)
        self.assertEqual(result.failed_shards, 1)
        self.assertEqual(result.took_ms, 7)
        self.assertEqual(result.mode, "hybrid")

        passage = result.candidates[0].evidence
        self.assertIsInstance(passage, RetrievalPassage)
        self.assertEqual(passage.scope, (frozenset({"win", "mac"}),))
        self.assertEqual(passage.provenance, {"lexical", "semantic"})
        self.assertEqual(passage.body_highlight.field, "content_text")

        question = result.candidates[1].evidence
        self.assertIsInstance(question, LegacyQuestion)
        self.assertEqual(question.num_answers, 1)
        self.assertEqual(question.provenance, frozenset())
        self.assertEqual(question.highlight.field, "question_content")

        request = client.search.call_args.kwargs
        self.assertTrue(request["allow_partial_search_results"])
        self.assertNotIn("content_vector", request["source_includes"])
        self.assertEqual(request["size"], 3)

        response["hits"]["hits"][0]["_source"]["scope"]["version"] = 2
        degraded = _decode_response(response, page_size=2, offset=0, mode="hybrid")
        self.assertEqual([candidate.family_id for candidate in degraded.candidates], ["aaq:9"])
        self.assertTrue(degraded.degraded)
        self.assertEqual(degraded.invalid_hit_count, 1)

        response["hits"]["hits"][0]["_source"]["scope"]["version"] = 1
        response["_shards"]["successful"] = 0
        with self.assertRaisesRegex(InvalidRetrievalResponse, "no Elasticsearch shard"):
            _decode_response(response, page_size=2, offset=0, mode="hybrid")

    def test_rejects_pages_outside_either_bound(self):
        common = {
            "query": "firefox",
            "kb_index": "retrieval-42",
            "locale": "en-US",
            "sources": {"kb"},
            "viewer_group_ids": (),
            "product_id": None,
            "query_vector": None,
            "similarity_floor": None,
            "semantic_k": 10,
            "num_candidates": 20,
            "locale_composition": "combined",
            "page_size": 2,
        }
        with self.assertRaisesRegex(ValueError, "max_offset"):
            _retrieve_unvalidated(**common, rank_window_size=20, offset=11, max_offset=10)
        with self.assertRaisesRegex(ValueError, "has_more"):
            _retrieve_unvalidated(**common, rank_window_size=10, offset=8, max_offset=10)


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
                        "heading_path": "Firefox > Startup",
                        "scope": {"version": 1, "clauses": []},
                        "visibility": "public",
                        "access_group_ids": [],
                        "product_ids": ["3"],
                        "topic_ids": ["7"],
                        "category": "10",
                        "title": {"en-US": "firefox startup crash"},
                        "summary": {"en-US": "fix a firefox startup crash"},
                        "content_text": {"en-US": f"firefox startup crash passage {position}"},
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
                        "heading_path": "Firefox > Safe mode",
                        "scope": {"version": 1, "clauses": []},
                        "visibility": "public",
                        "access_group_ids": [],
                        "product_ids": ["3"],
                        "topic_ids": ["7"],
                        "category": "10",
                        "title": {"en-US": "firefox startup crash"},
                        "summary": {"en-US": "fix a firefox startup crash"},
                        "content_text": {
                            "en-US": "short exact semantic firefox startup crash passage"
                        },
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
                        "answer_content": {"en-US": ["try firefox safe mode"]},
                        "question_created": now,
                        "question_updated": now,
                        "question_has_answers": True,
                        "question_has_solution": True,
                        "question_num_votes": 2,
                        "question_is_archived": False,
                        "question_product_id": 3,
                    },
                },
                {
                    "_index": ChunkDocument.Index.write_alias,
                    "_id": "manifest-1",
                    "_source": {
                        "kind": "manifest",
                        "content_type": "kb",
                        "object_id": "1",
                        "locale": "en-US",
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

        result = _retrieve_unvalidated(
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
            page_size=2,
            offset=0,
            max_offset=10,
            strict=True,
        )
        self.assertEqual(len(result.candidates), 2)
        self.assertEqual(result.approximate_total, 3)
        self.assertTrue(result.has_more)
        self.assertEqual(result.mode, "hybrid")
        self.assertTrue(
            all(
                candidate.family_id in {"kb:1", "kb:2", "aaq:3"} for candidate in result.candidates
            )
        )
        passages = [
            candidate.evidence
            for candidate in result.candidates
            if isinstance(candidate.evidence, RetrievalPassage)
        ]
        self.assertTrue(any(passage.body_highlight for passage in passages))

        aaq_result = _retrieve_unvalidated(
            "community troubleshooting",
            kb_index=None,
            locale="en-US",
            sources={"aaq"},
            viewer_group_ids=(),
            product_id=3,
            query_vector=None,
            similarity_floor=None,
            semantic_k=2,
            num_candidates=2,
            rank_window_size=2,
            locale_composition="combined",
            page_size=1,
            offset=0,
            max_offset=0,
            strict=True,
        )
        [aaq_candidate] = aaq_result.candidates
        self.assertIsInstance(aaq_candidate.evidence, LegacyQuestion)
        self.assertEqual(aaq_candidate.evidence.highlight.field, "question_content")
