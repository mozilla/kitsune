import json
import math
from unittest import mock

from django.core.exceptions import ImproperlyConfigured
from django.test import SimpleTestCase, override_settings
from google.genai.errors import ClientError, ServerError

from kitsune.retrieval.embeddings import (
    _MAX_ATTEMPTS,
    FAKE_BACKEND,
    VERTEX_BACKEND,
    EmbeddingRecipe,
    InvalidEmbeddingRecipe,
    InvalidEmbeddingResponse,
    _vertex_client,
    configured_embedding_recipe,
    get_embeddings,
    recipe_from_payload,
    recipe_to_payload,
    validate_embeddings,
)

FAKE = EmbeddingRecipe(
    provider=FAKE_BACKEND,
    model="fake-1",
    dimensions=8,
    document_task="RETRIEVAL_DOCUMENT",
    query_task="RETRIEVAL_QUERY",
    normalization="none",
)

VERTEX = EmbeddingRecipe(
    provider=VERTEX_BACKEND,
    model="text-embedding-005",
    dimensions=8,
    document_task="RETRIEVAL_DOCUMENT",
    query_task="RETRIEVAL_QUERY",
    normalization="none",
)


def _marker_vectors(batch, **kwargs):
    """A stand-in embedder: vector[0] = ord(first char), so order is checkable."""
    return [[float(ord(text[0])), *([0.0] * 7)] for text in batch]


class GetEmbeddingsFakeTests(SimpleTestCase):
    def test_empty_input_returns_empty(self):
        self.assertEqual(get_embeddings([], task="document", recipe=FAKE), [])

    def test_one_finite_vector_per_text_of_recipe_dimensions(self):
        vectors = get_embeddings(["a", "b", "c"], task="document", recipe=FAKE)

        self.assertEqual(len(vectors), 3)
        for vector in vectors:
            self.assertEqual(len(vector), FAKE.dimensions)
            self.assertTrue(all(math.isfinite(x) for x in vector))

    def test_deterministic_across_calls(self):
        first = get_embeddings(["reset password"], task="document", recipe=FAKE)
        second = get_embeddings(["reset password"], task="document", recipe=FAKE)
        self.assertEqual(first, second)

    def test_distinct_text_gives_distinct_vector(self):
        [alpha] = get_embeddings(["alpha"], task="document", recipe=FAKE)
        [beta] = get_embeddings(["beta"], task="document", recipe=FAKE)
        self.assertNotEqual(alpha, beta)

    def test_accepts_a_non_list_sequence(self):
        vectors = get_embeddings(("a", "b"), task="document", recipe=FAKE)
        self.assertEqual(len(vectors), 2)

    def test_document_and_query_encodings_differ(self):
        [document] = get_embeddings(["same text"], task="document", recipe=FAKE)
        [query] = get_embeddings(["same text"], task="query", recipe=FAKE)
        self.assertNotEqual(document, query)

    def test_l2_fake_is_normalized(self):
        recipe = EmbeddingRecipe(**{**recipe_to_payload(FAKE), "normalization": "l2"})
        [vector] = get_embeddings(["normalized"], task="document", recipe=recipe)
        self.assertAlmostEqual(math.sqrt(sum(value * value for value in vector)), 1.0)

    def test_rejects_unknown_task(self):
        with self.assertRaisesMessage(ValueError, "unknown embedding task"):
            get_embeddings(["a"], task="other", recipe=FAKE)  # type: ignore[arg-type]

    def test_rejects_non_string_input(self):
        with self.assertRaisesMessage(TypeError, "embedding inputs must be strings"):
            get_embeddings(["a", 1], task="document", recipe=FAKE)  # type: ignore[list-item]

    def test_rejects_a_string_instead_of_a_sequence_of_texts(self):
        with self.assertRaisesMessage(TypeError, "a sequence of strings"):
            get_embeddings("one input", task="document", recipe=FAKE)


class VertexBackendTests(SimpleTestCase):
    @override_settings(RETRIEVAL_EMBEDDING_BATCH_SIZE=2)
    def test_batches_and_preserves_order(self):
        client = mock.Mock()
        client.embed.side_effect = _marker_vectors

        with mock.patch(
            "kitsune.retrieval.embeddings._vertex_client", return_value=client
        ) as vertex_client:
            vectors = get_embeddings(["a", "b", "c", "d", "e"], task="document", recipe=VERTEX)

        self.assertEqual([v[0] for v in vectors], [97.0, 98.0, 99.0, 100.0, 101.0])
        self.assertEqual(client.embed.call_count, 3)  # 5 texts, batch size 2
        vertex_client.assert_called_once_with("text-embedding-005")
        first_call = client.embed.call_args_list[0]
        self.assertEqual(first_call.kwargs["embeddings_task_type"], "RETRIEVAL_DOCUMENT")
        self.assertEqual(first_call.kwargs["dimensions"], 8)

    def test_query_uses_query_task_type(self):
        client = mock.Mock()
        client.embed.side_effect = _marker_vectors

        with mock.patch("kitsune.retrieval.embeddings._vertex_client", return_value=client):
            get_embeddings(["how to reset"], task="query", recipe=VERTEX)

        self.assertEqual(client.embed.call_args.kwargs["embeddings_task_type"], "RETRIEVAL_QUERY")

    def test_empty_input_never_builds_a_client(self):
        with mock.patch(
            "kitsune.retrieval.embeddings._vertex_client",
            side_effect=AssertionError("client must not be built for empty input"),
        ):
            self.assertEqual(get_embeddings([], task="document", recipe=VERTEX), [])

    def test_fake_recipe_never_touches_vertex(self):
        with mock.patch(
            "kitsune.retrieval.embeddings._vertex_client",
            side_effect=AssertionError("fake path must not build a vertex client"),
        ):
            get_embeddings(["a", "b"], task="document", recipe=FAKE)

    @override_settings(RETRIEVAL_EMBEDDING_BATCH_SIZE=0)
    def test_rejects_non_positive_batch_size(self):
        with (
            mock.patch("kitsune.retrieval.embeddings._vertex_client") as vertex_client,
            self.assertRaises(ImproperlyConfigured),
        ):
            get_embeddings(["a"], task="document", recipe=VERTEX)
        vertex_client.assert_not_called()

    def test_malformed_batch_stops_before_later_provider_calls(self):
        client = mock.Mock()
        client.embed.return_value = []

        with (
            override_settings(RETRIEVAL_EMBEDDING_BATCH_SIZE=1),
            mock.patch("kitsune.retrieval.embeddings._vertex_client", return_value=client),
            self.assertRaises(InvalidEmbeddingResponse),
        ):
            get_embeddings(["a", "b"], task="document", recipe=VERTEX)

        client.embed.assert_called_once()

    def test_client_disables_its_nested_retry_loop(self):
        _vertex_client.cache_clear()
        with mock.patch("langchain_google_vertexai.VertexAIEmbeddings") as client_class:
            _vertex_client("text-embedding-005")
        _vertex_client.cache_clear()

        client_class.assert_called_once_with(model="text-embedding-005", max_retries=0)


class ValidateEmbeddingsTests(SimpleTestCase):
    def test_rejects_wrong_count(self):
        with self.assertRaises(InvalidEmbeddingResponse):
            validate_embeddings([[0.0] * 8], ["a", "b"], FAKE)

    def test_rejects_wrong_dimension(self):
        with self.assertRaises(InvalidEmbeddingResponse):
            validate_embeddings([[0.0] * 7], ["a"], FAKE)

    def test_rejects_non_finite(self):
        with self.assertRaises(InvalidEmbeddingResponse):
            validate_embeddings([[float("nan"), *([0.0] * 7)]], ["a"], FAKE)

    def test_rejects_infinity(self):
        with self.assertRaises(InvalidEmbeddingResponse):
            validate_embeddings([[float("inf"), *([0.0] * 7)]], ["a"], FAKE)

    def test_rejects_non_numeric_values(self):
        with self.assertRaises(InvalidEmbeddingResponse):
            validate_embeddings([["not-a-number", *([0.0] * 7)]], ["a"], FAKE)  # type: ignore[list-item]

    def test_l2_recipe_rejects_non_unit_norm(self):
        l2_recipe = EmbeddingRecipe(
            provider=FAKE_BACKEND,
            model="fake-1",
            dimensions=8,
            document_task="RETRIEVAL_DOCUMENT",
            query_task="RETRIEVAL_QUERY",
            normalization="l2",
        )
        with self.assertRaises(InvalidEmbeddingResponse):
            validate_embeddings([[2.0, *([0.0] * 7)]], ["a"], l2_recipe)


class ConfiguredRecipeTests(SimpleTestCase):
    @override_settings(
        RETRIEVAL_EMBEDDING_BACKEND=FAKE_BACKEND,
        RETRIEVAL_EMBEDDING_MODEL="",
        RETRIEVAL_EMBEDDING_DIMENSIONS=768,
    )
    def test_defaults_to_fake_backend(self):
        recipe = configured_embedding_recipe()
        self.assertEqual(recipe.provider, FAKE_BACKEND)
        self.assertEqual(recipe.dimensions, 768)
        self.assertEqual(recipe.document_task, "RETRIEVAL_DOCUMENT")
        self.assertEqual(recipe.query_task, "RETRIEVAL_QUERY")

    @override_settings(
        RETRIEVAL_EMBEDDING_BACKEND=VERTEX_BACKEND,
        RETRIEVAL_EMBEDDING_MODEL="text-embedding-005",
        RETRIEVAL_EMBEDDING_DIMENSIONS=768,
    )
    def test_builds_vertex_recipe_from_settings(self):
        recipe = configured_embedding_recipe()
        self.assertEqual(recipe.provider, VERTEX_BACKEND)
        self.assertEqual(recipe.model, "text-embedding-005")

    @override_settings(RETRIEVAL_EMBEDDING_BACKEND=VERTEX_BACKEND, RETRIEVAL_EMBEDDING_MODEL="")
    def test_vertex_without_model_fails_closed(self):
        with self.assertRaises(ImproperlyConfigured):
            configured_embedding_recipe()

    @override_settings(RETRIEVAL_EMBEDDING_BACKEND="bogus", RETRIEVAL_EMBEDDING_MODEL="x")
    def test_unknown_backend_fails_closed(self):
        with self.assertRaises(ImproperlyConfigured):
            configured_embedding_recipe()

    @override_settings(RETRIEVAL_EMBEDDING_BATCH_SIZE=0)
    def test_non_positive_batch_size_fails_closed(self):
        with self.assertRaises(ImproperlyConfigured):
            configured_embedding_recipe()


class RecipePayloadTests(SimpleTestCase):
    def test_round_trip_reconstructs_the_recipe(self):
        self.assertEqual(recipe_from_payload(recipe_to_payload(VERTEX)), VERTEX)

    def test_payload_is_json_serializable(self):
        payload = recipe_to_payload(VERTEX)
        self.assertEqual(recipe_from_payload(json.loads(json.dumps(payload))), VERTEX)

    def test_rejects_unknown_normalization(self):
        payload = {**recipe_to_payload(VERTEX), "normalization": "mystery"}
        with self.assertRaises(InvalidEmbeddingRecipe):
            recipe_from_payload(payload)

    def test_rejects_non_integer_dimensions(self):
        payload = {**recipe_to_payload(VERTEX), "dimensions": "768"}
        with self.assertRaises(InvalidEmbeddingRecipe):
            recipe_from_payload(payload)

    def test_rejects_missing_or_extra_fields(self):
        missing = recipe_to_payload(VERTEX)
        del missing["model"]
        with self.assertRaises(InvalidEmbeddingRecipe):
            recipe_from_payload(missing)

        extra = {**recipe_to_payload(VERTEX), "unexpected": True}
        with self.assertRaises(InvalidEmbeddingRecipe):
            recipe_from_payload(extra)


class VertexRetryTests(SimpleTestCase):
    def test_retries_transient_then_succeeds(self):
        client = mock.Mock()
        client.embed.side_effect = [
            ServerError(503, {"message": "busy"}),
            ServerError(503, {"message": "busy"}),
            [[1.0, *([0.0] * 7)]],
        ]
        with (
            mock.patch("kitsune.retrieval.embeddings._vertex_client", return_value=client),
            mock.patch("kitsune.retrieval.embeddings.time.sleep") as sleep,
        ):
            vectors = get_embeddings(["a"], task="document", recipe=VERTEX)

        self.assertEqual(len(vectors), 1)
        self.assertEqual(client.embed.call_count, 3)
        self.assertEqual(sleep.call_count, 2)

    def test_retries_rate_limit_then_succeeds(self):
        client = mock.Mock()
        client.embed.side_effect = [
            ClientError(429, {"message": "rate limited"}),
            [[1.0, *([0.0] * 7)]],
        ]
        with (
            mock.patch("kitsune.retrieval.embeddings._vertex_client", return_value=client),
            mock.patch("kitsune.retrieval.embeddings.time.sleep"),
        ):
            get_embeddings(["a"], task="document", recipe=VERTEX)

        self.assertEqual(client.embed.call_count, 2)

    def test_permanent_error_fails_without_retry(self):
        client = mock.Mock()
        client.embed.side_effect = ClientError(403, {"message": "nope"})
        with (
            mock.patch("kitsune.retrieval.embeddings._vertex_client", return_value=client),
            mock.patch("kitsune.retrieval.embeddings.time.sleep"),
            self.assertRaises(ClientError),
        ):
            get_embeddings(["a"], task="document", recipe=VERTEX)

        self.assertEqual(client.embed.call_count, 1)

    def test_gives_up_after_max_attempts(self):
        client = mock.Mock()
        client.embed.side_effect = ServerError(503, {"message": "busy"})
        with (
            mock.patch("kitsune.retrieval.embeddings._vertex_client", return_value=client),
            mock.patch("kitsune.retrieval.embeddings.time.sleep"),
            self.assertRaises(ServerError),
        ):
            get_embeddings(["a"], task="document", recipe=VERTEX)

        self.assertEqual(client.embed.call_count, _MAX_ATTEMPTS)
