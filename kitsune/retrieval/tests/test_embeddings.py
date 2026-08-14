import json
import math
from dataclasses import replace
from types import SimpleNamespace
from unittest import mock

from django.core.exceptions import ImproperlyConfigured
from django.test import SimpleTestCase, override_settings
from google.auth.exceptions import DefaultCredentialsError
from google.genai.errors import APIError, ClientError, ServerError
from httpx import ConnectError as HttpxConnectError
from httpx import ReadTimeout as HttpxReadTimeout

from kitsune.retrieval.embeddings import (
    _MAX_ATTEMPTS,
    FAKE_BACKEND,
    VERTEX_BACKEND,
    EmbeddingRecipe,
    EmbeddingUnavailable,
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


def _vertex_response(batch, *, truncated=False):
    vectors = _marker_vectors(batch)
    return SimpleNamespace(
        embeddings=[
            SimpleNamespace(
                values=vector,
                statistics=SimpleNamespace(truncated=truncated),
            )
            for vector in vectors
        ]
    )


def _mock_vertex_client():
    client = mock.Mock()
    client.model_name = VERTEX.model
    request = client.client.models.embed_content
    request.side_effect = lambda **kwargs: _vertex_response(kwargs["contents"])
    return client, request


class GetEmbeddingsFakeTests(SimpleTestCase):
    def test_empty_input_returns_empty(self):
        self.assertEqual(get_embeddings([], task="document", recipe=FAKE), [])

    def test_one_finite_vector_per_text_of_recipe_dimensions(self):
        vectors = get_embeddings(["a", "b", "c"], task="document", recipe=FAKE)

        self.assertEqual(len(vectors), 3)
        for vector in vectors:
            self.assertEqual(len(vector), FAKE.dimensions)
            self.assertTrue(all(math.isfinite(x) for x in vector))

    def test_is_deterministic_and_text_sensitive(self):
        first = get_embeddings(["reset password"], task="document", recipe=FAKE)
        second = get_embeddings(["reset password"], task="document", recipe=FAKE)
        self.assertEqual(first, second)

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
        client, request = _mock_vertex_client()

        with mock.patch(
            "kitsune.retrieval.embeddings._vertex_client", return_value=client
        ) as vertex_client:
            vectors = get_embeddings(["a", "b", "c", "d", "e"], task="document", recipe=VERTEX)

        self.assertEqual([v[0] for v in vectors], [97.0, 98.0, 99.0, 100.0, 101.0])
        self.assertEqual(request.call_count, 3)  # 5 texts, batch size 2
        vertex_client.assert_called_once_with("text-embedding-005")
        first_call = request.call_args_list[0]
        self.assertEqual(first_call.kwargs["model"], "text-embedding-005")
        self.assertEqual(first_call.kwargs["config"].task_type, "RETRIEVAL_DOCUMENT")
        self.assertEqual(first_call.kwargs["config"].output_dimensionality, 8)
        self.assertIs(first_call.kwargs["config"].auto_truncate, False)

    def test_batches_within_the_total_request_token_limit(self):
        client, request = _mock_vertex_client()
        texts = [chr(ord("a") + number) for number in range(11)]

        with (
            mock.patch("kitsune.retrieval.embeddings.count_tokens", return_value=2_000),
            mock.patch("kitsune.retrieval.embeddings._vertex_client", return_value=client),
        ):
            get_embeddings(texts, task="document", recipe=VERTEX)

        self.assertEqual(
            [len(call.kwargs["contents"]) for call in request.call_args_list],
            [10, 1],
        )

    @override_settings(RETRIEVAL_EMBEDDING_TIMEOUT_SECONDS=12)
    def test_every_request_carries_an_explicit_deadline(self):
        client, request = _mock_vertex_client()
        with mock.patch("kitsune.retrieval.embeddings._vertex_client", return_value=client):
            get_embeddings(["a"], task="document", recipe=VERTEX)

        http_options = request.call_args.kwargs["config"].http_options
        self.assertEqual(http_options.timeout, 12_000)  # the provider expects milliseconds

    def test_transport_errors_are_retried(self):
        for transient in (HttpxReadTimeout("timed out"), HttpxConnectError("connection reset")):
            with self.subTest(transient=type(transient).__name__):
                client, request = _mock_vertex_client()
                request.side_effect = [transient, _vertex_response(["a"])]
                with (
                    mock.patch("kitsune.retrieval.embeddings._vertex_client", return_value=client),
                    mock.patch("kitsune.retrieval.embeddings.time.sleep"),
                ):
                    vectors = get_embeddings(["a"], task="document", recipe=VERTEX)
                self.assertEqual(len(vectors), 1)
                self.assertEqual(request.call_count, 2)

    def test_an_unusable_timeout_fails_closed(self):
        for timeout in (0, -1, 0.0001, True, "1", float("inf"), float("nan")):
            with (
                self.subTest(timeout=timeout),
                override_settings(RETRIEVAL_EMBEDDING_TIMEOUT_SECONDS=timeout),
                mock.patch("kitsune.retrieval.embeddings._vertex_client") as vertex_client,
                self.assertRaises(ImproperlyConfigured),
            ):
                get_embeddings(["a"], task="document", recipe=VERTEX)
            vertex_client.assert_not_called()

    @override_settings(RETRIEVAL_EMBEDDING_TIMEOUT_SECONDS=0.001)
    def test_one_millisecond_is_the_minimum_timeout(self):
        client, request = _mock_vertex_client()
        with mock.patch("kitsune.retrieval.embeddings._vertex_client", return_value=client):
            get_embeddings(["a"], task="document", recipe=VERTEX)
        self.assertEqual(request.call_args.kwargs["config"].http_options.timeout, 1)

    @override_settings(RETRIEVAL_QUERY_EMBEDDING_TIMEOUT_SECONDS=2)
    def test_query_uses_query_task_type_and_deadline(self):
        client, request = _mock_vertex_client()

        with mock.patch("kitsune.retrieval.embeddings._vertex_client", return_value=client):
            get_embeddings(["how to reset"], task="query", recipe=VERTEX)

        config = request.call_args.kwargs["config"]
        self.assertEqual(config.task_type, "RETRIEVAL_QUERY")
        self.assertEqual(config.http_options.timeout, 2_000)

    def test_query_provider_failure_is_not_retried(self):
        for error in (
            ServerError(503, {"message": "busy"}),
            HttpxConnectError("connection failed"),
        ):
            with self.subTest(error=type(error).__name__):
                client, request = _mock_vertex_client()
                request.side_effect = error
                with (
                    mock.patch("kitsune.retrieval.embeddings._vertex_client", return_value=client),
                    mock.patch("kitsune.retrieval.embeddings.time.sleep") as sleep,
                    self.assertRaises(EmbeddingUnavailable),
                ):
                    get_embeddings(["how to reset"], task="query", recipe=VERTEX)

                request.assert_called_once()
                sleep.assert_not_called()

    def test_query_credential_failure_is_unavailable(self):
        with (
            mock.patch(
                "kitsune.retrieval.embeddings._vertex_client",
                side_effect=DefaultCredentialsError("credentials unavailable"),
            ),
            self.assertRaises(EmbeddingUnavailable),
        ):
            get_embeddings(["how to reset"], task="query", recipe=VERTEX)

    def test_query_invalid_response_is_unavailable(self):
        client, request = _mock_vertex_client()
        request.side_effect = None
        request.return_value = _vertex_response(["truncated"], truncated=True)
        with (
            mock.patch("kitsune.retrieval.embeddings._vertex_client", return_value=client),
            self.assertRaises(EmbeddingUnavailable),
        ):
            get_embeddings(["truncated"], task="query", recipe=VERTEX)

    def test_query_recipe_error_remains_a_correctness_failure(self):
        invalid = replace(VERTEX, provider="unknown")
        with self.assertRaises(InvalidEmbeddingRecipe):
            get_embeddings(["how to reset"], task="query", recipe=invalid)

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
        client, request = _mock_vertex_client()
        request.side_effect = None
        request.return_value = SimpleNamespace(embeddings=[])

        with (
            override_settings(RETRIEVAL_EMBEDDING_BATCH_SIZE=1),
            mock.patch("kitsune.retrieval.embeddings._vertex_client", return_value=client),
            self.assertRaises(InvalidEmbeddingResponse),
        ):
            get_embeddings(["a", "b"], task="document", recipe=VERTEX)

        request.assert_called_once()

    def test_rejects_estimated_input_over_the_provider_limit_before_calling_vertex(self):
        client, request = _mock_vertex_client()
        with (
            mock.patch("kitsune.retrieval.embeddings._vertex_client", return_value=client),
            self.assertRaisesRegex(InvalidEmbeddingResponse, "per-input token limit"),
        ):
            get_embeddings(["漢" * 2049], task="document", recipe=VERTEX)
        request.assert_not_called()

    def test_rejects_provider_reported_truncation(self):
        client, request = _mock_vertex_client()
        request.side_effect = None
        request.return_value = _vertex_response(["truncated"], truncated=True)
        with (
            mock.patch("kitsune.retrieval.embeddings._vertex_client", return_value=client),
            self.assertRaisesRegex(InvalidEmbeddingResponse, "truncated token statistics"),
        ):
            get_embeddings(["truncated"], task="document", recipe=VERTEX)

    def test_client_disables_its_nested_retry_loop(self):
        _vertex_client.cache_clear()
        with mock.patch("kitsune.retrieval.embeddings.VertexAIEmbeddings") as client_class:
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

    def test_rejects_non_finite_values(self):
        for value in (float("nan"), float("inf"), float("-inf")):
            with self.subTest(value=value), self.assertRaises(InvalidEmbeddingResponse):
                validate_embeddings([[value, *([0.0] * 7)]], ["a"], FAKE)

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
    def test_builds_fake_recipe_from_settings(self):
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

    @override_settings(RETRIEVAL_EMBEDDING_BACKEND="")
    def test_empty_backend_fails_closed(self):
        with self.assertRaises(ImproperlyConfigured):
            configured_embedding_recipe()

    @override_settings(RETRIEVAL_EMBEDDING_BATCH_SIZE=0)
    def test_non_positive_batch_size_fails_closed(self):
        with self.assertRaises(ImproperlyConfigured):
            configured_embedding_recipe()


class RecipePayloadTests(SimpleTestCase):
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
        client, request = _mock_vertex_client()
        request.side_effect = [
            ServerError(503, {"message": "busy"}),
            ServerError(503, {"message": "busy"}),
            _vertex_response(["a"]),
        ]
        with (
            mock.patch("kitsune.retrieval.embeddings._vertex_client", return_value=client),
            mock.patch("kitsune.retrieval.embeddings.time.sleep") as sleep,
        ):
            vectors = get_embeddings(["a"], task="document", recipe=VERTEX)

        self.assertEqual(len(vectors), 1)
        self.assertEqual(request.call_count, 3)
        self.assertEqual(sleep.call_count, 2)

    def test_retries_rate_limit_then_succeeds(self):
        client, request = _mock_vertex_client()
        request.side_effect = [
            ClientError(429, {"message": "rate limited"}),
            _vertex_response(["a"]),
        ]
        with (
            mock.patch("kitsune.retrieval.embeddings._vertex_client", return_value=client),
            mock.patch("kitsune.retrieval.embeddings.time.sleep"),
        ):
            get_embeddings(["a"], task="document", recipe=VERTEX)

        self.assertEqual(request.call_count, 2)

    def test_permanent_error_fails_without_retry(self):
        client, request = _mock_vertex_client()
        request.side_effect = ClientError(403, {"message": "nope"})
        with (
            mock.patch("kitsune.retrieval.embeddings._vertex_client", return_value=client),
            mock.patch("kitsune.retrieval.embeddings.time.sleep"),
            self.assertRaises(ClientError),
        ):
            get_embeddings(["a"], task="document", recipe=VERTEX)

        self.assertEqual(request.call_count, 1)

    def test_an_apierror_without_a_code_fails_without_retry(self):
        client, request = _mock_vertex_client()
        request.side_effect = APIError(None, {"message": "no status code"})
        with (
            mock.patch("kitsune.retrieval.embeddings._vertex_client", return_value=client),
            mock.patch("kitsune.retrieval.embeddings.time.sleep"),
            self.assertRaises(APIError),
        ):
            get_embeddings(["a"], task="document", recipe=VERTEX)

        self.assertEqual(request.call_count, 1)

    def test_gives_up_after_max_attempts(self):
        client, request = _mock_vertex_client()
        request.side_effect = ServerError(503, {"message": "busy"})
        with (
            mock.patch("kitsune.retrieval.embeddings._vertex_client", return_value=client),
            mock.patch("kitsune.retrieval.embeddings.time.sleep"),
            self.assertRaises(ServerError),
        ):
            get_embeddings(["a"], task="document", recipe=VERTEX)

        self.assertEqual(request.call_count, _MAX_ATTEMPTS)
