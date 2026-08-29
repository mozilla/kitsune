import logging
from contextlib import contextmanager
from dataclasses import replace
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
    HybridSearchSessionUnavailable,
    result_from_candidate,
    run_hybrid_search,
    sources_for_where,
)

RECIPE = EmbeddingRecipe("fake", "model", 2, "document", "query", "l2")
STANDARD_LOG_FIELDS = set(logging.makeLogRecord({}).__dict__) | {"asctime", "message"}
META = {"sentinel": "meta"}  # opaque to hybrid; handed to the floor resolver as-is


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


def _question_candidate(rank):
    family_id = f"aaq:{rank}"
    return AuthorizedCandidate(
        rank,
        1 / rank,
        family_id,
        LegacyQuestion(
            question_id=str(rank),
            family_id=family_id,
            locale="en-US",
            title=f"Question {rank}",
            content="Question content",
            updated=datetime.now(UTC),
            is_solved=True,
            num_answers=1,
            num_votes=2,
            provenance=frozenset({"lexical"}),
            highlight=None,
        ),
    )


@contextmanager
def _run(**patches):
    defaults = {
        "resolve_read_state": ("retrieval-1", RECIPE, META),
        "get_cached_query_vector": ([1.0, 0.0], "hit"),
        "similarity_floor_for_meta": 0.8,
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
            "kitsune.search.hybrid.resolve_read_state",
            return_value=defaults["resolve_read_state"],
        ) as target,
        mock.patch(
            "kitsune.search.hybrid.get_cached_query_vector",
            return_value=defaults["get_cached_query_vector"],
        ) as cached,
        mock.patch("kitsune.search.hybrid.is_ratelimited") as limited,
        mock.patch("kitsune.search.hybrid.embed_and_cache_query_vector") as embed,
        mock.patch(
            "kitsune.search.hybrid.similarity_floor_for_meta",
            return_value=defaults["similarity_floor_for_meta"],
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
        SEARCH_RESULTS_PER_PAGE=2,
        RETRIEVAL_SEARCH_SEGMENT_SIZE=2,
        RETRIEVAL_RRF_RANK_WINDOW_SIZE=3,
    )
    def test_continuation_extends_the_pinned_ranking_without_reembedding(self):
        first_segment = replace(
            _result(_question_candidate(1), _question_candidate(2)),
            approximate_total=4,
            has_more=True,
            encountered_family_ids=("aaq:1", "aaq:2"),
        )
        second_segment = replace(
            _result(_question_candidate(3), _question_candidate(4)),
            approximate_total=2,
            encountered_family_ids=("aaq:3", "aaq:4"),
        )
        with _run(retrieve=first_segment) as (_, cached, _, embed, _, retrieve):
            retrieve.side_effect = (first_segment, second_segment)
            first = run_hybrid_search(
                _request(),
                query="firefox",
                locale="en-US",
                sources={"kb", "aaq"},
                product_id=None,
                page=1,
            )
            second = run_hybrid_search(
                _request(),
                query="firefox",
                locale="en-US",
                sources={"kb", "aaq"},
                product_id=None,
                page=2,
                session_token=first.session_token,
            )

        self.assertIsNotNone(first.session_token)
        self.assertTrue(first.has_next)
        self.assertEqual([item["rank"] for item in first.results], [1, 2])
        self.assertEqual([item["rank"] for item in second.results], [3, 4])
        self.assertFalse(second.has_next)
        self.assertEqual(retrieve.call_count, 2)
        self.assertEqual(
            retrieve.call_args_list[1].kwargs["excluded_family_ids"],
            ("aaq:1", "aaq:2"),
        )
        cached.assert_called_once()
        embed.assert_not_called()

    @override_settings(
        SEARCH_RESULTS_PER_PAGE=3,
        RETRIEVAL_SEARCH_SEGMENT_SIZE=7,
        RETRIEVAL_RRF_RANK_WINDOW_SIZE=8,
    )
    def test_sequential_navigation_reaches_every_authorized_family_once(self):
        raw_candidates = tuple(_question_candidate(rank) for rank in range(1, 24))

        def retrieve_segment(*args, **kwargs):
            excluded = set(kwargs["excluded_family_ids"])
            remaining = tuple(
                candidate for candidate in raw_candidates if candidate.family_id not in excluded
            )
            raw_segment = remaining[:7]
            authorized = tuple(
                candidate
                for candidate in raw_segment
                if int(candidate.evidence.question_id) % 4
            )
            return replace(
                _result(*authorized),
                approximate_total=len(remaining),
                has_more=len(remaining) > len(raw_segment),
                encountered_family_ids=tuple(
                    candidate.family_id for candidate in raw_segment
                ),
            )

        with _run(retrieve=_result()) as (_, _, _, _, _, retrieve):
            retrieve.side_effect = retrieve_segment
            page = 1
            token = None
            presented = []
            while True:
                result = run_hybrid_search(
                    _request(),
                    query="firefox",
                    locale="en-US",
                    sources={"aaq"},
                    product_id=None,
                    page=page,
                    session_token=token,
                )
                token = result.session_token
                presented.extend(result.results)
                if not result.has_next:
                    break
                page += 1

            retrieval_calls = retrieve.call_count
            first_page_again = run_hybrid_search(
                _request(),
                query="firefox",
                locale="en-US",
                sources={"aaq"},
                product_id=None,
                page=1,
                session_token=token,
            )

        expected_ids = [rank for rank in range(1, 24) if rank % 4]
        self.assertEqual(
            [int(item["url"].rstrip("/").split("/")[-1]) for item in presented],
            expected_ids,
        )
        self.assertEqual([item["rank"] for item in presented], list(range(1, 19)))
        self.assertEqual([item["rank"] for item in first_page_again.results], [1, 2, 3])
        self.assertEqual(retrieval_calls, 4)
        self.assertEqual(retrieve.call_count, retrieval_calls)

    @override_settings(
        SEARCH_RESULTS_PER_PAGE=2,
        RETRIEVAL_SEARCH_SEGMENT_SIZE=3,
        RETRIEVAL_RRF_RANK_WINDOW_SIZE=4,
    )
    def test_reading_a_pinned_page_refreshes_without_replacing_the_session(self):
        segment = _result(*(_question_candidate(rank) for rank in range(1, 4)))
        with _run(retrieve=segment) as (_, _, _, _, _, retrieve):
            first = run_hybrid_search(
                _request(),
                query="firefox",
                locale="en-US",
                sources={"aaq"},
                product_id=None,
                page=1,
            )
            with (
                mock.patch("kitsune.search.hybrid.cache.set") as store,
                mock.patch("kitsune.search.hybrid.cache.touch", return_value=True) as touch,
            ):
                repeated = run_hybrid_search(
                    _request(),
                    query="firefox",
                    locale="en-US",
                    sources={"aaq"},
                    product_id=None,
                    page=1,
                    session_token=first.session_token,
                )

        self.assertEqual(repeated.results, first.results)
        self.assertEqual(retrieve.call_count, 1)
        store.assert_not_called()
        touch.assert_called_once()

    @override_settings(
        SEARCH_RESULTS_PER_PAGE=2,
        RETRIEVAL_SEARCH_SEGMENT_SIZE=3,
        RETRIEVAL_RRF_RANK_WINDOW_SIZE=4,
    )
    def test_short_segment_page_does_not_hide_later_candidates(self):
        first_segment = replace(
            _result(*(_question_candidate(rank) for rank in range(1, 4))),
            approximate_total=5,
            has_more=True,
            encountered_family_ids=("aaq:1", "aaq:2", "aaq:3"),
        )
        second_segment = replace(
            _result(_question_candidate(4), _question_candidate(5)),
            approximate_total=2,
            encountered_family_ids=("aaq:4", "aaq:5"),
        )
        with _run(retrieve=first_segment) as (_, _, _, _, _, retrieve):
            retrieve.side_effect = (first_segment, second_segment)
            first = run_hybrid_search(
                _request(),
                query="firefox",
                locale="en-US",
                sources={"aaq"},
                product_id=None,
                page=1,
            )
            second = run_hybrid_search(
                _request(),
                query="firefox",
                locale="en-US",
                sources={"aaq"},
                product_id=None,
                page=2,
                session_token=first.session_token,
            )
            third = run_hybrid_search(
                _request(),
                query="firefox",
                locale="en-US",
                sources={"aaq"},
                product_id=None,
                page=3,
                session_token=first.session_token,
            )

        self.assertEqual([item["rank"] for item in first.results], [1, 2])
        self.assertEqual([item["rank"] for item in second.results], [3])
        self.assertEqual([item["rank"] for item in third.results], [4, 5])
        self.assertFalse(third.has_next)
        self.assertEqual(retrieve.call_count, 2)

    def test_missing_continuation_never_restarts_as_a_different_ranking(self):
        with (
            _run(retrieve=_result()) as (_, _, _, _, _, retrieve),
            self.assertNoLogs("k.retrieval", level="ERROR"),
            self.assertRaises(HybridSearchSessionUnavailable),
        ):
            run_hybrid_search(
                _request(),
                query="firefox",
                locale="en-US",
                sources={"kb"},
                product_id=None,
                page=2,
                session_token="missing-search-session-token",
            )

        retrieve.assert_not_called()

    @override_settings(
        SEARCH_RESULTS_PER_PAGE=2,
        RETRIEVAL_SEARCH_SEGMENT_SIZE=3,
        RETRIEVAL_RRF_RANK_WINDOW_SIZE=4,
    )
    def test_search_session_cannot_cross_viewer_access_boundaries(self):
        segment = _result(*(_question_candidate(rank) for rank in range(1, 4)))
        with _run(retrieve=segment):
            first = run_hybrid_search(
                _request(),
                query="firefox",
                locale="en-US",
                sources={"aaq"},
                product_id=None,
                page=1,
            )

        with (
            _run(retrieve=segment, viewer_access_for=ViewerAccess((7,))) as (
                _,
                _,
                _,
                _,
                _,
                retrieve,
            ),
            self.assertRaises(HybridSearchSessionUnavailable),
        ):
            run_hybrid_search(
                _request(),
                query="firefox",
                locale="en-US",
                sources={"aaq"},
                product_id=None,
                page=2,
                session_token=first.session_token,
            )

        self.assertIsNotNone(first.session_token)
        retrieve.assert_not_called()

    def test_cache_write_failure_does_not_render_broken_pagination(self):
        segment = replace(
            _result(*(_question_candidate(rank) for rank in range(1, 12))),
            approximate_total=20,
            has_more=True,
        )
        with (
            _run(retrieve=segment),
            mock.patch("kitsune.search.hybrid.cache.set", return_value=False),
        ):
            result = run_hybrid_search(
                _request(),
                query="firefox",
                locale="en-US",
                sources={"aaq"},
                product_id=None,
                page=2,
            )

        self.assertIsNone(result.session_token)
        self.assertFalse(result.has_previous)
        self.assertFalse(result.has_next)
        self.assertEqual(result.approximate_total, 1)

    def test_single_page_does_not_create_an_unused_search_session(self):
        with (
            _run(retrieve=_result(_question_candidate(1))),
            mock.patch("kitsune.search.hybrid.cache.set") as store,
        ):
            result = run_hybrid_search(
                _request(),
                query="firefox",
                locale="en-US",
                sources={"aaq"},
                product_id=None,
                page=1,
            )

        self.assertIsNone(result.session_token)
        self.assertFalse(result.has_previous)
        self.assertFalse(result.has_next)
        store.assert_not_called()

    @override_settings(
        RETRIEVAL_SEMANTIC_K=11,
        RETRIEVAL_KNN_NUM_CANDIDATES=23,
        RETRIEVAL_RRF_RANK_WINDOW_SIZE=40,
        RETRIEVAL_SEARCH_SEGMENT_SIZE=25,
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
        floor.assert_called_once_with(META)
        retrieval_settings = {
            "semantic_k": 11,
            "num_candidates": 23,
            "rank_window_size": 40,
            "locale_composition": "separate",
            "default_operator": "OR",
            "minimum_should_match": "2<-1",
        }
        self.assertEqual(
            {name: retrieve.call_args.kwargs[name] for name in retrieval_settings},
            retrieval_settings,
        )
        self.assertEqual(retrieve.call_args.kwargs["query_vector"], (1.0, 0.0))
        self.assertEqual(retrieve.call_args.kwargs["page_size"], 25)
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
            # The floor is resolved for every KB request before any vector work.
            floor.assert_called_once_with(META)
            self.assertEqual(
                retrieve.call_args.kwargs["query_vector"],
                tuple(vector) if vector is not None else None,
            )
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
    def test_missing_similarity_floor_degrades_to_lexical_without_spending(self):
        with _run() as (_, cached, limited, embed, floor, retrieve):
            floor.side_effect = SimilarityFloorUnavailable("missing")
            with self.assertLogs("k.retrieval", level="WARNING") as logs:
                result = run_hybrid_search(
                    _request(),
                    query="firefox",
                    locale="en-US",
                    sources={"kb"},
                    product_id=None,
                    page=1,
                )

        # Without a floor there is no bounded kNN: no cache read, no limiter hit, no spend.
        cached.assert_not_called()
        limited.assert_not_called()
        embed.assert_not_called()
        self.assertIsNone(retrieve.call_args.kwargs["query_vector"])
        self.assertIsNone(retrieve.call_args.kwargs["similarity_floor"])
        self.assertEqual(result.fallback_reason, "similarity_floor_unavailable")
        self.assertIsNone(result.query_vector_cache_lookup)
        self.assertIsNone(result.query_vector_cache_write)
        [record] = logs.records
        self.assertEqual(record.getMessage(), "retrieval.query.degraded")
        self.assertEqual(record.reason, "similarity_floor_unavailable")

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
