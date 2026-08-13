import re
from pathlib import Path
from unittest import mock
from uuid import uuid4

from django.test import SimpleTestCase, override_settings
from google.genai.errors import ServerError
from redis.exceptions import ConnectionError as RedisConnectionError

import kitsune.retrieval
import kitsune.search.hybrid
from kitsune.retrieval.embeddings import get_embeddings
from kitsune.retrieval.events import EVENT_CATALOG, UnknownEvent, emit
from kitsune.retrieval.gate import gate_index
from kitsune.retrieval.index import ChunkDocument, ChunkIdentity
from kitsune.retrieval.locks import (
    DocumentLockBackendError,
    DocumentLockUnavailable,
    document_lock,
    redis_lease,
)
from kitsune.retrieval.sync import sync_document_batch, sync_document_chunks
from kitsune.retrieval.tests import ChunkIndexTestCase
from kitsune.retrieval.tests.test_embeddings import (
    VERTEX,
    _mock_vertex_client,
    _vertex_response,
)
from kitsune.sumo.redis_utils import RedisError, redis_client
from kitsune.users.tests import GroupFactory
from kitsune.wiki.tests import ApprovedRevisionFactory, DocumentFactory

_EMIT_CALL = re.compile(r"\bemit\(\s*\"([a-z0-9_.]+)\"", re.S)

# Field names that would defeat the point of the whole surface. Checked against every record
# every seam emits, not just against the helper's own validation.
_FORBIDDEN_FIELDS = frozenset(
    {
        "access_group_ids",
        "content",
        "content_text",
        "content_vector",
        "credentials",
        "group_ids",
        "groups",
        "html",
        "key",
        "keywords",
        "password",
        "restrict_to_groups",
        "secret",
        "summary",
        "text",
        "title",
        "token",
        "vector",
        "vectors",
    }
)


def _emitted_event_names():
    """Every event name the package can emit, read from the source rather than from imports."""
    package = Path(kitsune.retrieval.__file__).parent
    paths = [*package.rglob("*.py"), Path(kitsune.search.hybrid.__file__)]
    names = set()
    for path in paths:
        if "tests" in path.parts:
            continue
        names.update(_EMIT_CALL.findall(path.read_text()))
    return names


def _event(logs, name):
    [event] = [record for record in logs.records if record.getMessage() == name]
    return event


class EventCatalogTests(SimpleTestCase):
    """The catalog is the audit. An event the package emits but does not document — or
    documents but no longer emits — is a defect, not a detail."""

    def test_the_catalog_and_the_source_agree_exactly(self):
        self.assertSetEqual(_emitted_event_names(), set(EVENT_CATALOG))

    def test_an_uncatalogued_event_is_refused_at_runtime(self):
        # Otherwise a typo ships as a new event name nobody is aggregating on.
        with self.assertRaises(UnknownEvent):
            emit("retrieval.sync.complted")

    def test_every_catalogued_name_is_namespaced(self):
        for name in EVENT_CATALOG:
            with self.subTest(event=name):
                self.assertTrue(name.startswith("retrieval."))


class ProviderEventTests(SimpleTestCase):
    """The provider is the one seam that costs money, so its size and latency are observable."""

    @override_settings(RETRIEVAL_EMBEDDING_BATCH_SIZE=1)
    def test_a_completed_request_reports_size_and_latency_but_never_the_text(self):
        client, _ = _mock_vertex_client()
        with (
            mock.patch("kitsune.retrieval.embeddings._vertex_client", return_value=client),
            self.assertLogs("k.retrieval", level="INFO") as logs,
        ):
            get_embeddings(["hello", "world!"], task="document", recipe=VERTEX)

        record = _event(logs, "retrieval.embeddings.completed")
        self.assertEqual(record.text_count, 2)
        self.assertEqual(record.character_count, 11)
        self.assertEqual(record.request_count, 2)
        self.assertGreaterEqual(record.duration_ms, 0)
        self.assertNotIn("hello", repr(record.__dict__))
        for field in _FORBIDDEN_FIELDS:
            self.assertNotIn(field, record.__dict__)

    def test_a_retry_reports_the_error_type_and_not_its_message(self):
        client, request = _mock_vertex_client()
        request.side_effect = [
            ServerError(503, {"message": "busy: secret-token-abc123"}),
            _vertex_response(["a"]),
        ]
        with (
            mock.patch("kitsune.retrieval.embeddings._vertex_client", return_value=client),
            mock.patch("kitsune.retrieval.embeddings.time.sleep"),
            self.assertLogs("k.retrieval", level="INFO") as logs,
        ):
            get_embeddings(["a"], task="document", recipe=VERTEX)

        record = _event(logs, "retrieval.embeddings.retried")
        self.assertEqual(record.error_type, "ServerError")
        self.assertEqual(_event(logs, "retrieval.embeddings.completed").request_count, 2)
        self.assertNotIn("secret-token-abc123", repr(record.__dict__))

    def test_a_failure_reports_the_error_type_and_not_its_message(self):
        client, request = _mock_vertex_client()
        request.side_effect = RuntimeError("credentials=secret-token-abc123")
        with (
            mock.patch("kitsune.retrieval.embeddings._vertex_client", return_value=client),
            self.assertLogs("k.retrieval", level="ERROR") as logs,
            self.assertRaises(RuntimeError),
        ):
            get_embeddings(["a"], task="document", recipe=VERTEX)

        record = _event(logs, "retrieval.embeddings.failed")
        self.assertEqual(record.character_count, 1)
        self.assertEqual(record.request_count, 1)
        self.assertEqual(record.error_type, "RuntimeError")
        self.assertNotIn("secret-token-abc123", repr(record.__dict__))


class LockEventTests(SimpleTestCase):
    """A lease that cannot be taken or held is why work stalls, so it is never silent."""

    def setUp(self):
        super().setUp()
        self.client = redis_client("default")
        self.key = f"retrieval:test-lease:{uuid4().hex}"
        self.addCleanup(self.client.delete, self.key)

    def test_contention_is_reported(self):
        with redis_lease(self.key):
            with self.assertLogs("k.retrieval", level="WARNING") as logs:
                with self.assertRaises(DocumentLockUnavailable):
                    with redis_lease(self.key):
                        pass

        record = _event(logs, "retrieval.lock.contended")
        self.assertEqual(record.lock_kind, "other")
        self.assertNotIn(self.key, repr(record.__dict__))

    def test_a_lost_lease_is_reported(self):
        with redis_lease(self.key) as lease:
            self.client.delete(self.key)  # stand-in for the ttl elapsing
            with self.assertLogs("k.retrieval", level="WARNING") as logs:
                with self.assertRaises(DocumentLockUnavailable):
                    lease.renew()

        self.assertEqual(_event(logs, "retrieval.lock.lost").lock_kind, "other")

    def test_an_unreachable_backend_is_reported(self):
        with (
            mock.patch("kitsune.retrieval.locks._lock_client", side_effect=RedisError("no redis")),
            self.assertLogs("k.retrieval", level="ERROR") as logs,
            self.assertRaises(DocumentLockBackendError),
        ):
            with redis_lease(self.key):
                pass

        record = _event(logs, "retrieval.lock.backend_unavailable")
        self.assertEqual(record.operation, "acquire")
        self.assertEqual(record.lock_kind, "other")

    def test_a_release_backend_failure_is_reported_before_cleanup_swallows_it(self):
        with redis_lease(self.key) as lease:
            broken = mock.Mock()
            broken.release.side_effect = RedisConnectionError("connection lost")
            with (
                mock.patch.object(lease, "_lock", broken),
                self.assertLogs("k.retrieval", level="ERROR") as logs,
                self.assertRaises(DocumentLockBackendError),
            ):
                lease.release()

        record = _event(logs, "retrieval.lock.backend_unavailable")
        self.assertEqual(record.operation, "release")
        self.assertEqual(record.lock_kind, "other")
        self.assertEqual(record.error_type, "ConnectionError")


class ObservabilityTestCase(ChunkIndexTestCase):
    def setUp(self):
        super().setUp()
        self.index = ChunkDocument.alias_points_at(ChunkDocument.Index.write_alias)
        self.document = DocumentFactory(title="Install Firefox", slug="install-firefox")
        ApprovedRevisionFactory(document=self.document, summary="How to install.")
        self.document.refresh_from_db()
        self.identity = ChunkIdentity("kb", str(self.document.id), self.document.locale)


class ApprovalLatencyTests(ObservabilityTestCase):
    def test_a_commit_reports_how_long_since_the_revision_was_approved(self):
        with self.assertLogs("k.retrieval", level="INFO") as logs:
            sync_document_chunks(self.document.id)

        record = _event(logs, "retrieval.sync.completed")
        # The whole write path's freshness SLI: approval to searchable.
        self.assertIsNotNone(record.approval_latency_ms)
        self.assertGreaterEqual(record.approval_latency_ms, 0)

    def test_an_eviction_reports_no_latency_rather_than_a_misleading_one(self):
        sync_document_chunks(self.document.id)
        self.document.restrict_to_groups.add(GroupFactory())

        with self.assertLogs("k.retrieval", level="INFO") as logs:
            sync_document_chunks(self.document.id)

        record = _event(logs, "retrieval.sync.completed")
        self.assertIsNone(record.approval_latency_ms)


class CrossCuttingPrivacyTests(ObservabilityTestCase):
    """Audit a composed ingestion flow; seam tests cover the exceptional events."""

    def test_no_seam_emits_article_text_vectors_or_restriction_identifiers(self):
        group = GroupFactory(id=987_654_321, name="Confidential Partner Staff")
        secrets = ("Install Firefox", "How to install.", group.name, str(group.id))

        with self.assertLogs("k.retrieval", level="INFO") as logs:
            sync_document_chunks(self.document.id)
            sync_document_batch([self.document.id])
            gate_index(self.index)
            self.document.restrict_to_groups.add(group)
            sync_document_chunks(self.document.id)
            gate_index(self.index)
            with document_lock(self.identity), self.assertRaises(DocumentLockUnavailable):
                sync_document_chunks(self.document.id)

        self.assertGreater(len(logs.records), 6)
        for record in logs.records:
            rendered = repr(record.__dict__)
            with self.subTest(event=record.getMessage()):
                for field in _FORBIDDEN_FIELDS:
                    self.assertNotIn(field, record.__dict__)
                for secret in secrets:
                    self.assertNotIn(secret, rendered)
