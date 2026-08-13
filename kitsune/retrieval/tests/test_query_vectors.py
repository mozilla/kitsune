from dataclasses import replace
from unittest import mock

from django.core.cache import cache
from django.test import SimpleTestCase, override_settings

from kitsune.retrieval.checks import query_configuration_problems
from kitsune.retrieval.embeddings import FAKE_BACKEND, EmbeddingRecipe
from kitsune.retrieval.query_vectors import (
    embed_and_cache_query_vector,
    get_cached_query_vector,
)

RECIPE = EmbeddingRecipe(
    provider=FAKE_BACKEND,
    model="fake-1",
    dimensions=8,
    document_task="RETRIEVAL_DOCUMENT",
    query_task="RETRIEVAL_QUERY",
    normalization="none",
)


class QueryVectorCacheTests(SimpleTestCase):
    def setUp(self):
        cache.clear()

    def tearDown(self):
        cache.clear()

    def test_cache_is_scoped_to_the_exact_query_and_query_recipe(self):
        vector, cached = embed_and_cache_query_vector("Firefox crashes", RECIPE)

        self.assertEqual(cached, "stored")
        self.assertEqual(get_cached_query_vector("Firefox crashes", RECIPE), (vector, "hit"))
        self.assertEqual(get_cached_query_vector("Firefox crashes ", RECIPE), (None, "miss"))
        self.assertEqual(
            get_cached_query_vector(
                "Firefox crashes", replace(RECIPE, query_task="OTHER_QUERY_TASK")
            ),
            (None, "miss"),
        )

    @override_settings(RETRIEVAL_QUERY_VECTOR_CACHE_TTL_SECONDS=3600)
    def test_cache_key_hides_the_query_and_uses_the_configured_ttl(self):
        query = "private-looking but public query"
        vector = [0.0] * RECIPE.dimensions
        with (
            mock.patch("kitsune.retrieval.query_vectors.get_embeddings", return_value=[vector]),
            mock.patch("kitsune.retrieval.query_vectors.cache.set") as cache_set,
        ):
            self.assertEqual(embed_and_cache_query_vector(query, RECIPE), (vector, "stored"))

        key, cached = cache_set.call_args.args
        self.assertNotIn(query, key)
        self.assertEqual(cached, vector)
        self.assertEqual(cache_set.call_args.kwargs["timeout"], 3600)

    def test_invalid_or_unavailable_cache_is_a_miss(self):
        with (
            mock.patch("kitsune.retrieval.query_vectors.cache.get", return_value=[0.0]),
            mock.patch("kitsune.retrieval.query_vectors.cache.delete") as delete,
        ):
            self.assertEqual(get_cached_query_vector("query", RECIPE), (None, "invalid"))
        delete.assert_called_once()

        with mock.patch(
            "kitsune.retrieval.query_vectors.cache.get", side_effect=RuntimeError("offline")
        ):
            self.assertEqual(get_cached_query_vector("query", RECIPE), (None, "read_failed"))

    def test_cache_write_failure_still_returns_the_new_vector(self):
        vector = [0.0] * RECIPE.dimensions
        with (
            mock.patch("kitsune.retrieval.query_vectors.get_embeddings", return_value=[vector]),
            mock.patch(
                "kitsune.retrieval.query_vectors.cache.set", side_effect=RuntimeError("offline")
            ),
        ):
            self.assertEqual(
                embed_and_cache_query_vector("query", RECIPE),
                (vector, "write_failed"),
            )


class QueryConfigurationTests(SimpleTestCase):
    def test_invalid_timeout_and_ttl_are_reported(self):
        for setting, value in (
            ("RETRIEVAL_QUERY_EMBEDDING_TIMEOUT_SECONDS", 0),
            ("RETRIEVAL_QUERY_VECTOR_CACHE_TTL_SECONDS", 0),
        ):
            with self.subTest(setting=setting), override_settings(**{setting: value}):
                self.assertTrue(query_configuration_problems())

    def test_invalid_retrieval_bounds_are_reported(self):
        for setting, value in (
            ("RETRIEVAL_SEMANTIC_K", 0),
            ("RETRIEVAL_KNN_NUM_CANDIDATES", True),
            ("RETRIEVAL_RRF_RANK_WINDOW_SIZE", -1),
        ):
            with self.subTest(setting=setting), override_settings(**{setting: value}):
                self.assertTrue(query_configuration_problems())

        with override_settings(RETRIEVAL_SEMANTIC_K=20, RETRIEVAL_KNN_NUM_CANDIDATES=10):
            self.assertTrue(query_configuration_problems())

    def test_invalid_serving_policy_is_reported(self):
        for setting, value in (
            ("RETRIEVAL_AUTHORIZATION_OVERFETCH", -1),
            ("RETRIEVAL_MAX_PAGE_OFFSET", -1),
            ("RETRIEVAL_LEXICAL_DEFAULT_OPERATOR", "XOR"),
            ("RETRIEVAL_LEXICAL_MINIMUM_SHOULD_MATCH", ""),
            ("RETRIEVAL_LOCALE_COMPOSITION", "weighted"),
            ("RETRIEVAL_QUERY_EMBEDDING_RATE", "ten/m"),
        ):
            with self.subTest(setting=setting), override_settings(**{setting: value}):
                self.assertTrue(query_configuration_problems())

        with override_settings(
            RETRIEVAL_RRF_RANK_WINDOW_SIZE=20,
            RETRIEVAL_MAX_PAGE_OFFSET=10,
            RETRIEVAL_AUTHORIZATION_OVERFETCH=5,
        ):
            self.assertTrue(query_configuration_problems())

    def test_invalid_similarity_floor_mapping_is_reported(self):
        for floors in (
            {"not-a-fingerprint": 0.8},
            {"a" * 64: float("inf")},
            {"a" * 64: -1.01},
            {"a" * 64: 1.01},
            [],
        ):
            with (
                self.subTest(floors=floors),
                override_settings(RETRIEVAL_KNN_SIMILARITY_FLOORS=floors),
            ):
                self.assertTrue(query_configuration_problems())
