import logging
from contextlib import contextmanager
from datetime import UTC, datetime
from unittest import mock

from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import ImproperlyConfigured
from django.test import RequestFactory, SimpleTestCase, override_settings

from kitsune.retrieval.access import (
    AuthorizedCandidate,
    AuthorizedPassage,
    DisplayDocument,
    ViewerAccess,
)
from kitsune.retrieval.embeddings import EmbeddingRecipe, EmbeddingUnavailable
from kitsune.retrieval.query import (
    HighlightFragment,
    LegacyQuestion,
    RetrievalPassage,
    RetrievalResult,
    SimilarityFloorUnavailable,
)
from kitsune.search import SNIPPET_LENGTH
from kitsune.search.hybrid import (
    result_from_candidate,
    run_hybrid_search,
    sources_for_where,
)

RECIPE = EmbeddingRecipe("fake", "model", 2, "document", "query", "l2")
STANDARD_LOG_FIELDS = set(logging.makeLogRecord({}).__dict__) | {"asctime", "message"}


def _result(*candidates, degraded=False, invalid_hits=0, authorization_rejections=0, db_ms=0):
    return RetrievalResult(
        candidates=candidates,
        approximate_total=len(candidates),
        has_more=False,
        mode="lexical",
        degraded=degraded,
        failed_shards=1 if degraded else 0,
        took_ms=7,
        invalid_hit_count=invalid_hits,
        authorization_rejection_count=authorization_rejections,
        db_ms=db_ms,
    )


def _request():
    request = RequestFactory().get("/search?q=firefox")
    request.user = AnonymousUser()
    return request


@contextmanager
def _run(**patches):
    defaults = {
        "resolve_read_target_and_recipe": ("retrieval-1", RECIPE),
        "get_cached_query_vector": ([1.0, 0.0], "hit"),
        "cached_similarity_floor": 0.8,
        "retrieve": _result(
            degraded=True,
            invalid_hits=2,
            authorization_rejections=3,
            db_ms=4,
        ),
        "viewer_access_for": ViewerAccess(),
    }
    defaults.update(patches)
    with (
        mock.patch(
            "kitsune.search.hybrid.resolve_read_target_and_recipe",
            return_value=defaults["resolve_read_target_and_recipe"],
        ) as target,
        mock.patch(
            "kitsune.search.hybrid.get_cached_query_vector",
            return_value=defaults["get_cached_query_vector"],
        ) as cached,
        mock.patch("kitsune.search.hybrid.is_ratelimited") as limited,
        mock.patch("kitsune.search.hybrid.embed_and_cache_query_vector") as embed,
        mock.patch(
            "kitsune.search.hybrid.cached_similarity_floor",
            return_value=defaults["cached_similarity_floor"],
        ) as floor,
        mock.patch(
            "kitsune.search.hybrid.viewer_access_for",
            return_value=defaults["viewer_access_for"],
        ),
        mock.patch(
            "kitsune.search.hybrid.retrieve",
            return_value=defaults["retrieve"],
        ) as retrieve,
    ):
        yield target, cached, limited, embed, floor, retrieve


class HybridOrchestrationTests(SimpleTestCase):
    def test_existing_tabs_map_to_explicit_sources(self):
        self.assertEqual(sources_for_where(1), {"kb"})
        self.assertEqual(sources_for_where(2), {"aaq"})
        self.assertEqual(sources_for_where(3), {"kb", "aaq"})
        with self.assertRaises(ValueError):
            sources_for_where(4)

    @override_settings(
        RETRIEVAL_SEMANTIC_K=11,
        RETRIEVAL_KNN_NUM_CANDIDATES=23,
        RETRIEVAL_RRF_RANK_WINDOW_SIZE=40,
        RETRIEVAL_AUTHORIZATION_OVERFETCH=4,
        RETRIEVAL_MAX_PAGE_OFFSET=25,
        RETRIEVAL_LOCALE_COMPOSITION="separate",
        RETRIEVAL_LEXICAL_DEFAULT_OPERATOR="OR",
        RETRIEVAL_LEXICAL_MINIMUM_SHOULD_MATCH="2<-1",
    )
    def test_cache_hit_avoids_limiter_and_preserves_bounded_diagnostics(self):
        with (
            _run() as (target, cached, limited, embed, floor, retrieve),
            self.assertLogs("k.retrieval", level="INFO") as logs,
        ):
            result = run_hybrid_search(
                _request(),
                query="firefox",
                locale="en-US",
                sources={"kb", "aaq"},
                product_id=3,
                page=2,
            )

        target.assert_called_once_with()
        cached.assert_called_once_with("firefox", RECIPE)
        limited.assert_not_called()
        embed.assert_not_called()
        floor.assert_called_once_with("retrieval-1")
        retrieval_settings = {
            "semantic_k": 11,
            "num_candidates": 23,
            "rank_window_size": 40,
            "authorization_overfetch": 4,
            "max_offset": 25,
            "locale_composition": "separate",
            "default_operator": "OR",
            "minimum_should_match": "2<-1",
        }
        self.assertEqual(
            {name: retrieve.call_args.kwargs[name] for name in retrieval_settings},
            retrieval_settings,
        )
        self.assertEqual(retrieve.call_args.kwargs["query_vector"], [1.0, 0.0])
        self.assertEqual(retrieve.call_args.kwargs["offset"], 10)
        self.assertEqual(result.query_vector_cache_lookup, "hit")
        self.assertIsNone(result.query_vector_cache_write)
        self.assertTrue(result.degraded)
        self.assertEqual(result.failed_shards, 1)
        self.assertEqual(result.es_took_ms, 7)
        [event] = [
            record for record in logs.records if record.getMessage() == "retrieval.query.completed"
        ]
        self.assertEqual(event.outcome, "degraded")
        self.assertEqual(event.mode, "lexical")
        self.assertEqual(event.kb_result_count, 0)
        self.assertEqual(event.aaq_result_count, 0)
        self.assertEqual(event.failed_shard_count, 1)
        self.assertEqual(event.invalid_hit_count, 2)
        self.assertEqual(event.authorization_rejection_count, 3)
        self.assertGreaterEqual(event.db_ms, 4)
        self.assertEqual(event.cache_lookup, "hit")
        self.assertIsNone(event.cache_write)
        self.assertSetEqual(
            set(event.__dict__) - STANDARD_LOG_FIELDS,
            {
                "aaq_result_count",
                "authorization_rejection_count",
                "cache_lookup",
                "cache_write",
                "db_ms",
                "embedding_ms",
                "es_ms",
                "failed_shard_count",
                "fallback_reason",
                "kb_result_count",
                "locale_fallback_count",
                "mode",
                "outcome",
                "invalid_hit_count",
                "requested_locale",
                "total_ms",
            },
        )
        self.assertNotIn("firefox", repr(event.__dict__))

    @override_settings(RETRIEVAL_QUERY_EMBEDDING_RATE="10/m")
    def test_paid_miss_embeds_once_while_expected_failures_use_lexical(self):
        cases = (
            (False, [0.0, 1.0], None, None),
            (True, None, None, "rate_limited"),
            (False, None, EmbeddingUnavailable("offline"), "embedding_unavailable"),
            (RuntimeError("cache offline"), None, None, "rate_limit_unavailable"),
        )
        for limiter, vector, error, fallback in cases:
            with (
                self.subTest(fallback=fallback),
                _run(
                    get_cached_query_vector=(None, "miss"),
                    retrieve=_result(),
                ) as (
                    _,
                    _,
                    limited,
                    embed,
                    floor,
                    retrieve,
                ),
                self.assertLogs("k.retrieval", level="INFO") as logs,
            ):
                limited.side_effect = limiter if isinstance(limiter, Exception) else None
                limited.return_value = limiter if isinstance(limiter, bool) else False
                embed.return_value = (vector, "stored") if vector is not None else None
                embed.side_effect = error
                result = run_hybrid_search(
                    _request(),
                    query="firefox",
                    locale="en-US",
                    sources={"kb"},
                    product_id=None,
                    page=1,
                )

            if limiter is False:
                embed.assert_called_once_with("firefox", RECIPE)
                self.assertEqual(limited.call_args.kwargs["group"], "retrieval-query-embedding")
                self.assertEqual(limited.call_args.kwargs["key"], "user_or_ip")
                self.assertNotIn("method", limited.call_args.kwargs)
            else:
                embed.assert_not_called()
            if limiter is False:
                floor.assert_called_once_with("retrieval-1")
            else:
                floor.assert_not_called()
            self.assertEqual(retrieve.call_args.kwargs["query_vector"], vector)
            self.assertEqual(result.fallback_reason, fallback)
            self.assertEqual(result.query_vector_cache_lookup, "miss")
            self.assertEqual(
                result.query_vector_cache_write,
                "stored" if vector is not None else None,
            )
            [event] = [
                record
                for record in logs.records
                if record.getMessage() == "retrieval.query.completed"
            ]
            self.assertEqual(event.fallback_reason, fallback)
            self.assertEqual(event.outcome, "fallback" if fallback else "success")
            self.assertEqual(event.cache_lookup, "miss")
            self.assertEqual(event.cache_write, "stored" if vector is not None else None)

    @override_settings(RETRIEVAL_QUERY_EMBEDDING_RATE="10/m")
    def test_cache_lookup_and_write_failures_remain_distinct(self):
        with (
            _run(
                get_cached_query_vector=(None, "read_failed"),
                retrieve=_result(),
            ) as (_, _, limited, embed, _, _),
            self.assertLogs("k.retrieval", level="INFO") as logs,
        ):
            limited.return_value = False
            embed.return_value = ([0.0, 1.0], "write_failed")
            result = run_hybrid_search(
                _request(),
                query="firefox",
                locale="en-US",
                sources={"kb"},
                product_id=None,
                page=1,
            )

        self.assertEqual(result.query_vector_cache_lookup, "read_failed")
        self.assertEqual(result.query_vector_cache_write, "write_failed")
        [event] = [
            record for record in logs.records if record.getMessage() == "retrieval.query.completed"
        ]
        self.assertEqual(event.cache_lookup, "read_failed")
        self.assertEqual(event.cache_write, "write_failed")

    @override_settings(RETRIEVAL_QUERY_EMBEDDING_RATE="10/m")
    def test_cache_and_rate_limit_failures_leave_lexical_search_available(self):
        with (
            _run(
                get_cached_query_vector=(None, "read_failed"),
                retrieve=_result(),
            ) as (
                _,
                _,
                limited,
                embed,
                _,
                retrieve,
            ),
            self.assertLogs("k.retrieval", level="INFO") as logs,
        ):
            limited.side_effect = RuntimeError("redis leaked-message")
            result = run_hybrid_search(
                _request(),
                query="private-looking query",
                locale="en-US",
                sources={"kb"},
                product_id=None,
                page=1,
            )

        embed.assert_not_called()
        self.assertIsNone(retrieve.call_args.kwargs["query_vector"])
        self.assertEqual(result.mode, "lexical")
        self.assertEqual(result.fallback_reason, "rate_limit_unavailable")
        self.assertEqual(result.query_vector_cache_lookup, "read_failed")
        self.assertIsNone(result.query_vector_cache_write)
        [event] = [
            record for record in logs.records if record.getMessage() == "retrieval.query.completed"
        ]
        self.assertEqual(event.outcome, "fallback")
        self.assertNotIn("private-looking query", repr(event.__dict__))
        self.assertNotIn("leaked-message", repr(event.__dict__))

    def test_hard_failure_reports_only_phase_and_exception_type(self):
        with (
            _run() as (_, _, _, _, _, retrieve),
            self.assertLogs("k.retrieval", level="ERROR") as logs,
            self.assertRaisesRegex(RuntimeError, "provider leaked-message"),
        ):
            retrieve.side_effect = RuntimeError("provider leaked-message")
            run_hybrid_search(
                _request(),
                query="private-looking query",
                locale="en-US",
                sources={"kb"},
                product_id=None,
                page=1,
            )

        [event] = logs.records
        self.assertEqual(event.getMessage(), "retrieval.query.failed")
        self.assertEqual(event.phase, "retrieval")
        self.assertEqual(event.error_type, "RuntimeError")
        self.assertGreaterEqual(event.total_ms, 0)
        self.assertSetEqual(
            set(event.__dict__) - STANDARD_LOG_FIELDS,
            {"error_type", "phase", "total_ms"},
        )
        self.assertNotIn("private-looking query", repr(event.__dict__))
        self.assertNotIn("leaked-message", repr(event.__dict__))

    def test_observability_failure_does_not_change_the_search_outcome(self):
        with (
            _run(retrieve=_result()) as (_, _, _, _, _, retrieve),
            mock.patch("kitsune.search.hybrid.emit", side_effect=RuntimeError("logging offline")),
        ):
            result = run_hybrid_search(
                _request(),
                query="firefox",
                locale="en-US",
                sources={"kb"},
                product_id=None,
                page=1,
            )
            retrieve.side_effect = ValueError("original failure")
            with self.assertRaisesMessage(ValueError, "original failure"):
                run_hybrid_search(
                    _request(),
                    query="firefox",
                    locale="en-US",
                    sources={"kb"},
                    product_id=None,
                    page=1,
                )

        self.assertEqual(result.mode, "lexical")

    def test_zero_rate_disables_semantic_and_invalid_rate_fails_visibly(self):
        with (
            override_settings(RETRIEVAL_QUERY_EMBEDDING_RATE="0/s"),
            _run(get_cached_query_vector=(None, "miss")) as (_, _, limited, embed, _, _),
        ):
            result = run_hybrid_search(
                _request(),
                query="firefox",
                locale="en-US",
                sources={"kb"},
                product_id=None,
                page=1,
            )

        limited.assert_not_called()
        embed.assert_not_called()
        self.assertEqual(result.fallback_reason, "rate_limited")

        with (
            override_settings(RETRIEVAL_QUERY_EMBEDDING_RATE="ten/m"),
            _run(get_cached_query_vector=(None, "miss")) as (_, _, limited, embed, _, retrieve),
            self.assertRaises(ImproperlyConfigured),
        ):
            run_hybrid_search(
                _request(),
                query="firefox",
                locale="en-US",
                sources={"kb"},
                product_id=None,
                page=1,
            )

        limited.assert_not_called()
        embed.assert_not_called()
        retrieve.assert_not_called()

    @override_settings(RETRIEVAL_QUERY_EMBEDDING_RATE="10/m")
    def test_missing_similarity_floor_fails_before_paid_embedding(self):
        with _run(get_cached_query_vector=(None, "miss")) as (
            _,
            _,
            limited,
            embed,
            floor,
            retrieve,
        ):
            limited.return_value = False
            floor.side_effect = SimilarityFloorUnavailable("missing")
            with self.assertRaises(SimilarityFloorUnavailable):
                run_hybrid_search(
                    _request(),
                    query="firefox",
                    locale="en-US",
                    sources={"kb"},
                    product_id=None,
                    page=1,
                )
        embed.assert_not_called()
        retrieve.assert_not_called()

    def test_aaq_only_skips_the_retrieval_index_and_embedding_path(self):
        with _run() as (target, cached, limited, embed, floor, retrieve):
            result = run_hybrid_search(
                _request(),
                query="firefox",
                locale="de",
                sources={"aaq"},
                product_id=None,
                page=1,
            )

        target.assert_not_called()
        cached.assert_not_called()
        limited.assert_not_called()
        embed.assert_not_called()
        floor.assert_not_called()
        self.assertIsNone(retrieve.call_args.kwargs["kb_index"])
        self.assertIsNone(result.query_vector_cache_lookup)
        self.assertIsNone(result.query_vector_cache_write)


class ResultConversionTests(SimpleTestCase):
    def test_authorized_evidence_uses_the_safe_snippet_policy(self):
        truncated_html = "a" * (SNIPPET_LENGTH - 1) + "&hello"
        safe_truncation = "a" * (SNIPPET_LENGTH - 1) + "&amp;"
        display_de = DisplayDocument(2, "de", "Titel", "artikel", "Display summary")
        truncated_display = DisplayDocument(3, "de", "Titel", "artikel", truncated_html)
        display_en = DisplayDocument(1, "en-US", "Title", "article", "English summary")

        def candidate(
            rank,
            *,
            display=display_de,
            scope=(),
            provenance=frozenset({"lexical"}),
            body=None,
            summary=None,
            text="Plain passage",
        ):
            passage = RetrievalPassage(
                content_type="kb",
                object_id=str(display.document_id),
                family_id="kb:1",
                locale="de",
                position=0,
                heading_path="",
                scope=scope,
                text=text,
                provenance=provenance,
                body_highlight=(HighlightFragment("content_text", "de", body) if body else None),
                summary_highlight=(
                    HighlightFragment("summary", "de", summary) if summary else None
                ),
                product_ids=(),
                topic_ids=(),
                category="10",
            )
            return AuthorizedCandidate(
                rank,
                0.03,
                "kb:1",
                AuthorizedPassage(passage, display),
            )

        candidates = (
            candidate(1, body="<strong>Body</strong><script>bad</script>"),
            candidate(2, summary="<strong>Summary</strong>"),
            candidate(3, provenance=frozenset({"semantic"}), text=truncated_html),
            candidate(4, display=truncated_display),
            candidate(5, scope=(frozenset({"win11"}),), body="Scoped body"),
            candidate(6, display=display_en, body="Cross-locale body"),
        )
        summaries = [result_from_candidate(item, "de")["search_summary"] for item in candidates]

        self.assertIn("<strong>Body</strong>", summaries[0])
        self.assertNotIn("<script>", summaries[0])
        self.assertEqual(summaries[1], "<strong>Summary</strong>")
        self.assertEqual(summaries[2], safe_truncation)
        self.assertEqual(summaries[3], safe_truncation)
        self.assertEqual(summaries[4], "Display summary")
        self.assertEqual(summaries[5], "English summary")

        question = LegacyQuestion(
            question_id="9",
            family_id="aaq:9",
            locale="de",
            title="Question",
            content="Question content",
            updated=datetime.now(UTC),
            is_solved=True,
            num_answers=2,
            num_votes=3,
            provenance=frozenset({"lexical"}),
            highlight=HighlightFragment("question_content", "de", "<strong>Question</strong>"),
        )
        converted = result_from_candidate(
            AuthorizedCandidate(7, 0.02, "aaq:9", question),
            "de",
        )
        self.assertEqual(converted["search_summary"], "<strong>Question</strong>")
        self.assertEqual(converted["rank"], 7)
        self.assertNotIn("score", converted)
