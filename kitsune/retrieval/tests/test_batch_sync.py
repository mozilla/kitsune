from datetime import UTC, datetime
from unittest import mock

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.test import SimpleTestCase, override_settings

from kitsune.celery import app
from kitsune.products.tests import ProductFactory
from kitsune.retrieval.chunking import chunk
from kitsune.retrieval.embeddings import (
    EmbeddingRecipe,
    configured_embedding_recipe,
    get_embeddings,
    recipe_to_payload,
)
from kitsune.retrieval.fingerprints import build_index_meta
from kitsune.retrieval.index import (
    SCHEMA_VERSION,
    SIMILARITY,
    VECTOR_INDEX_OPTIONS,
    ChunkDocument,
    ChunkIdentity,
    IndexWriteError,
    configured_index_meta,
    create_write_generation,
    read_indexed_document,
)
from kitsune.retrieval.locks import (
    DocumentLockBackendError,
    DocumentLockUnavailable,
    RedisLease,
    document_lock,
    document_lock_key,
)
from kitsune.retrieval.sync import (
    BatchSyncReport,
    SyncOutcome,
    sync_document_batch,
    sync_document_chunks,
)
from kitsune.retrieval.tasks import enqueue_document_batch, sync_documents
from kitsune.retrieval.tests import ChunkIndexTestCase
from kitsune.sumo.redis_utils import redis_client
from kitsune.users.tests import GroupFactory
from kitsune.wiki.tests import ApprovedRevisionFactory, DocumentFactory


def _max_diff(first, second):
    """Vectors make a float32 round trip through ES, so compare them within that tolerance."""
    return max(abs(a - b) for a, b in zip(first, second, strict=True))


class BatchInputTests(SimpleTestCase):
    """Malformed input fails before any index, provider, or lease work."""

    def test_invalid_document_id_inputs_are_rejected(self):
        invalid = ("123", b"123", None, 7, object(), [None], ["3"], [3.5], [True], [object()])
        for document_ids in invalid:
            with self.subTest(document_ids=document_ids), self.assertRaises(TypeError):
                sync_document_batch(document_ids)

    def test_an_empty_batch_reports_nothing_and_pays_nothing(self):
        report = sync_document_batch([])

        self.assertEqual(report, BatchSyncReport())
        self.assertEqual(report.embedding_calls, 0)

    def test_an_invalid_bound_is_refused_rather_than_guessed(self):
        for setting in ("RETRIEVAL_BULK_MAX_DOCUMENTS", "RETRIEVAL_BULK_MAX_EMBEDDING_INPUTS"):
            for value in (0, -1, True, 2.5, "50", None):
                with (
                    self.subTest(setting=setting, value=value),
                    override_settings(**{setting: value}),
                    self.assertRaises(ImproperlyConfigured),
                ):
                    sync_document_batch([1])


class BatchTestCase(ChunkIndexTestCase):
    def setUp(self):
        super().setUp()
        self.index = ChunkDocument.alias_points_at(ChunkDocument.Index.write_alias)
        self.documents = [
            self._document("Install Firefox", "install-firefox", "How to install the browser."),
            self._document("Sync bookmarks", "sync-bookmarks", "How to sync your bookmarks."),
            self._document("Clear cookies", "clear-cookies", "How to clear stored cookies."),
        ]
        self.ids = [document.id for document in self.documents]

    def _document(self, title, slug, content):
        document = DocumentFactory(title=title, slug=slug)
        ApprovedRevisionFactory(document=document, content=content, summary=f"{title} summary")
        document.refresh_from_db()
        return document

    def _identity(self, document):
        return ChunkIdentity("kb", str(document.id), document.locale)

    def _stored(self, document, index=None):
        return read_indexed_document(index=index or self.index, identity=self._identity(document))

    def _texts(self, document):
        return [item.text for item in chunk("kb", document.html, title=document.title)]

    def _assert_embeds(self, document, recipe, index=None):
        """Every stored vector is the embedding of that document's own chunk text."""
        texts = self._texts(document)
        stored = self._stored(document, index).chunks
        self.assertEqual(len(stored), len(texts))
        expected = get_embeddings(texts, task="document", recipe=recipe)
        for item, want in zip(stored, expected, strict=True):
            self.assertLess(_max_diff(item["content_vector"], want), 1e-5)


class BatchExecutorTests(BatchTestCase):
    """The batch against real Elasticsearch, real leases, and the deterministic fake."""

    def test_one_shared_call_covers_every_document(self):
        with mock.patch(
            "kitsune.retrieval.sync.get_embeddings", side_effect=get_embeddings
        ) as embed:
            report = sync_document_batch(self.ids)

        self.assertEqual(embed.call_count, 1)
        self.assertEqual(report.embedding_calls, 1)
        self.assertEqual(
            {document_id: report.reports[document_id].outcome for document_id in self.ids},
            dict.fromkeys(self.ids, SyncOutcome.EMBED_REPLACE),
        )

    def test_the_flattened_inputs_are_every_documents_chunks_in_id_order(self):
        expected = [text for document in self.documents for text in self._texts(document)]

        with mock.patch(
            "kitsune.retrieval.sync.get_embeddings", side_effect=get_embeddings
        ) as embed:
            sync_document_batch(reversed(self.ids))

        self.assertEqual(embed.call_args.args[0], expected)

    def test_every_document_is_stored_with_the_vectors_for_its_own_text(self):
        sync_document_batch(self.ids)

        recipe = configured_embedding_recipe()
        for document in self.documents:
            with self.subTest(document=document.slug):
                self._assert_embeds(document, recipe)

    def test_duplicate_ids_are_synced_once(self):
        with mock.patch(
            "kitsune.retrieval.sync.get_embeddings", side_effect=get_embeddings
        ) as embed:
            report = sync_document_batch([self.ids[0], self.ids[0], self.ids[0]])

        self.assertEqual(list(report.reports), [self.ids[0]])
        self.assertEqual(embed.call_args.args[0], self._texts(self.documents[0]))

    def test_leases_are_acquired_in_ascending_document_order(self):
        with mock.patch(
            "kitsune.retrieval.sync.document_lock", side_effect=document_lock
        ) as acquire:
            sync_document_batch(reversed(self.ids))

        self.assertEqual(
            [call.args[0].object_id for call in acquire.call_args_list],
            [str(document_id) for document_id in sorted(self.ids)],
        )

    def test_an_explicit_target_does_not_fan_out(self):
        report = sync_document_batch(self.ids, target_index=self.index)

        for document_id in self.ids:
            self.assertEqual(report.reports[document_id].index, self.index)

    def test_no_write_target_writes_nothing(self):
        with (
            mock.patch("kitsune.retrieval.sync.resolve_write_target", return_value=None),
            self.assertLogs("k.retrieval", level="WARNING") as logs,
        ):
            report = sync_document_batch(self.ids)

        self.assertEqual(report.reports, {})
        self.assertEqual(report.embedding_calls, 0)
        self.assertEqual(logs.records[0].getMessage(), "retrieval.batch.skipped")

    def test_an_unchanged_document_costs_nothing_while_the_others_embed(self):
        sync_document_chunks(self.ids[0])

        report = sync_document_batch(self.ids)

        self.assertEqual(report.reports[self.ids[0]].outcome, SyncOutcome.NO_OP)
        self.assertEqual(report.embedding_calls, 1)
        self.assertEqual(report.reports[self.ids[1]].outcome, SyncOutcome.EMBED_REPLACE)

    def test_a_metadata_change_alone_pays_the_provider_nothing(self):
        sync_document_batch(self.ids)
        self.documents[0].products.add(ProductFactory())

        report = sync_document_batch(self.ids)

        self.assertEqual(report.reports[self.ids[0]].outcome, SyncOutcome.METADATA_ONLY)
        self.assertEqual(report.embedding_calls, 0)
        self.assertNotEqual(self._stored(self.documents[0]).chunks[0]["product_ids"], [])

    def test_a_deleted_row_is_evicted_without_stopping_the_batch(self):
        sync_document_batch(self.ids)
        missing = self.ids[0]
        self.documents[0].delete()

        report = sync_document_batch(self.ids)

        self.assertEqual(report.reports[missing].outcome, SyncOutcome.DELETED)
        self.assertEqual(self._stored(self.documents[0]).chunks, [])
        self.assertIsNotNone(self._stored(self.documents[1]).manifest)

    def test_an_ineligible_document_is_evicted_and_costs_no_input(self):
        sync_document_batch(self.ids)
        self.documents[0].restrict_to_groups.add(GroupFactory())
        ApprovedRevisionFactory(document=self.documents[1], content="Fresh content to embed.")
        self.documents[1].refresh_from_db()

        with mock.patch(
            "kitsune.retrieval.sync.get_embeddings", side_effect=get_embeddings
        ) as embed:
            report = sync_document_batch(self.ids)

        self.assertEqual(report.reports[self.ids[0]].outcome, SyncOutcome.DELETED)
        self.assertEqual(self._stored(self.documents[0]).chunks, [])
        self.assertEqual(embed.call_args.args[0], self._texts(self.documents[1]))

    def test_a_contended_document_costs_nothing_while_the_others_commit(self):
        with (
            document_lock(self._identity(self.documents[0])),
            mock.patch(
                "kitsune.retrieval.sync.get_embeddings", side_effect=get_embeddings
            ) as embed,
        ):
            report = sync_document_batch(self.ids)

        self.assertEqual(report.contended, (self.ids[0],))
        self.assertNotIn(self.ids[0], report.reports)
        self.assertEqual(self._stored(self.documents[0]).chunks, [])
        flattened = embed.call_args.args[0]
        for text in self._texts(self.documents[0]):
            self.assertNotIn(text, flattened)
        for document in self.documents[1:]:
            self.assertIsNotNone(self._stored(document).manifest)

    def test_a_lease_lost_mid_batch_is_reported_without_dropping_the_others(self):
        stolen = self.ids[1]
        real_renew = RedisLease.renew

        def renew(lease):
            if lease._key == document_lock_key(self._identity(self.documents[1])):
                raise DocumentLockUnavailable("stolen")
            real_renew(lease)

        with mock.patch.object(RedisLease, "renew", renew):
            report = sync_document_batch(self.ids)

        self.assertEqual(report.contended, (stolen,))
        self.assertEqual(self._stored(self.documents[1]).chunks, [])
        for document in (self.documents[0], self.documents[2]):
            self.assertIsNotNone(self._stored(document).manifest)

    def test_a_lock_backend_outage_aborts_the_whole_batch(self):
        # Redis is also the broker: if ownership cannot be proven for one document it cannot be
        # proven for any, so the batch fails and Celery retries it.
        with (
            mock.patch.object(
                RedisLease, "renew", side_effect=DocumentLockBackendError("redis down")
            ),
            self.assertRaises(DocumentLockBackendError),
        ):
            sync_document_batch(self.ids)

    def test_each_document_is_revalidated_after_the_shared_call(self):
        def edit_then_embed(*args, **kwargs):
            ApprovedRevisionFactory(document=self.documents[1], content="Raced edit.")
            return get_embeddings(*args, **kwargs)

        with mock.patch("kitsune.retrieval.sync.get_embeddings", side_effect=edit_then_embed):
            report = sync_document_batch(self.ids)

        self.assertEqual(report.reports[self.ids[1]].outcome, SyncOutcome.ABORTED_STALE)
        self.assertEqual(self._stored(self.documents[1]).chunks, [])
        for document in (self.documents[0], self.documents[2]):
            self.assertIsNotNone(self._stored(document).manifest)

    def test_a_restriction_during_the_shared_call_evicts_that_document_only(self):
        sync_document_batch(self.ids)
        for document in self.documents:
            ApprovedRevisionFactory(document=document, content=f"New body for {document.slug}.")
            document.refresh_from_db()

        def restrict_then_embed(*args, **kwargs):
            self.documents[2].restrict_to_groups.add(GroupFactory())
            return get_embeddings(*args, **kwargs)

        with mock.patch("kitsune.retrieval.sync.get_embeddings", side_effect=restrict_then_embed):
            report = sync_document_batch(self.ids)

        self.assertEqual(report.reports[self.ids[2]].outcome, SyncOutcome.DELETED)
        self.assertEqual(self._stored(self.documents[2]).chunks, [])
        self.assertIsNotNone(self._stored(self.documents[0]).manifest)

    def test_every_lease_is_released_even_when_a_write_fails(self):
        client = redis_client("default")

        with (
            mock.patch(
                "kitsune.retrieval.sync.replace_chunks", side_effect=IndexWriteError("bulk failed")
            ),
            self.assertRaises(IndexWriteError),
        ):
            sync_document_batch(self.ids)

        for document in self.documents:
            with self.subTest(document=document.slug):
                self.assertIsNone(client.get(document_lock_key(self._identity(document))))

    def test_a_provider_failure_commits_nothing(self):
        with (
            mock.patch(
                "kitsune.retrieval.sync.get_embeddings", side_effect=RuntimeError("provider down")
            ),
            self.assertRaises(RuntimeError),
        ):
            sync_document_batch(self.ids)

        for document in self.documents:
            self.assertIsNone(self._stored(document).manifest)

    def test_invalid_target_metadata_does_not_block_eviction_of_an_ineligible_document(self):
        sync_document_batch(self.ids)
        self.documents[0].restrict_to_groups.add(GroupFactory())

        with (
            mock.patch(
                "kitsune.retrieval.sync.recipe_for_index",
                side_effect=ImproperlyConfigured("bad index metadata"),
            ),
            self.assertRaises(ImproperlyConfigured),
        ):
            sync_document_batch(self.ids)

        self.assertEqual(self._stored(self.documents[0]).chunks, [])


class BatchEventTests(BatchTestCase):
    def test_events_summarize_the_batch_and_each_document_without_sensitive_payloads(self):
        with self.assertLogs("k.retrieval", level="INFO") as logs:
            sync_document_batch(self.ids)

        [record] = [r for r in logs.records if r.getMessage() == "retrieval.batch.completed"]
        self.assertEqual(record.document_count, len(self.ids))
        self.assertEqual(record.synced, len(self.ids))
        self.assertEqual(record.embedding_calls, 1)
        self.assertEqual(record.outcomes, {SyncOutcome.EMBED_REPLACE.value: len(self.ids)})
        for title in ("Install Firefox", "Sync bookmarks", "Clear cookies"):
            self.assertNotIn(title, repr(record.__dict__))
        for field in ("content_text", "content_vector", "access_group_ids", "title"):
            self.assertNotIn(field, record.__dict__)

        completions = [r for r in logs.records if r.getMessage() == "retrieval.sync.completed"]
        self.assertEqual(
            sorted(record.object_id for record in completions),
            sorted(str(document_id) for document_id in self.ids),
        )


@override_settings(RETRIEVAL_BULK_MAX_DOCUMENTS=2)
class BatchBoundTests(BatchTestCase):
    def test_documents_past_the_document_limit_are_deferred_without_being_touched(self):
        with self.assertLogs("k.retrieval", level="WARNING") as logs:
            report = sync_document_batch(self.ids)

        deferred = next(d for d in self.documents if d.id == sorted(self.ids)[2])
        self.assertEqual(len(report.reports), 2)
        self.assertEqual(report.deferred, (deferred.id,))
        self.assertEqual(self._stored(deferred).chunks, [])
        [record] = [r for r in logs.records if r.getMessage() == "retrieval.batch.deferred"]
        self.assertEqual(record.over_document_limit, 1)
        self.assertEqual(record.over_input_limit, 0)

    @override_settings(RETRIEVAL_BULK_MAX_DOCUMENTS=10, RETRIEVAL_BULK_MAX_EMBEDDING_INPUTS=1)
    def test_documents_past_the_input_limit_are_deferred(self):
        report = sync_document_batch(self.ids)

        self.assertEqual(len(report.reports), 1)
        self.assertEqual(len(report.deferred), 2)
        self.assertEqual(report.embedding_calls, 1)

    @override_settings(RETRIEVAL_BULK_MAX_DOCUMENTS=10, RETRIEVAL_BULK_MAX_EMBEDDING_INPUTS=1)
    def test_a_document_bigger_than_the_input_limit_still_makes_progress(self):
        # Otherwise an article with more chunks than the bound could never be indexed.
        body = "\n\n".join(
            f"Step {i} describes one distinct configuration detail in careful prose."
            for i in range(120)
        )
        big = self._document("Long guide", "long-guide", body)
        self.assertGreater(len(self._texts(big)), 1)

        report = sync_document_batch([big.id])

        self.assertEqual(report.deferred, ())
        self.assertEqual(len(self._stored(big).chunks), len(self._texts(big)))

    @override_settings(RETRIEVAL_BULK_MAX_DOCUMENTS=10, RETRIEVAL_BULK_MAX_EMBEDDING_INPUTS=1)
    def test_a_deferred_document_does_not_keep_its_lease(self):
        client = redis_client("default")
        held = []

        def record_then_embed(*args, **kwargs):
            held.extend(
                document.id
                for document in self.documents
                if client.get(document_lock_key(self._identity(document)))
            )
            return get_embeddings(*args, **kwargs)

        with mock.patch("kitsune.retrieval.sync.get_embeddings", side_effect=record_then_embed):
            report = sync_document_batch(self.ids)

        for document_id in report.deferred:
            self.assertNotIn(document_id, held)


class BatchSingleWriteGenerationTests(BatchTestCase):
    """A batch also writes only to the current write generation."""

    def _second_generation(self, recipe=None):
        meta = (
            configured_index_meta()
            if recipe is None
            else build_index_meta(
                recipe,
                similarity=SIMILARITY,
                index_options=VECTOR_INDEX_OPTIONS,
                schema_version=SCHEMA_VERSION,
            )
        )
        return create_write_generation(timestamp=datetime(2031, 5, 4, tzinfo=UTC), meta=meta)

    def test_a_batch_populates_only_the_write_generation(self):
        second = self._second_generation()

        report = sync_document_batch(self.ids)

        self.assertEqual(report.embedding_calls, 1)
        for document in self.documents:
            self.assertIsNone(self._stored(document, self.index).manifest)
            self.assertIsNotNone(self._stored(document, second).manifest)

    def test_a_batch_uses_only_the_write_generations_recipe(self):
        other_space = EmbeddingRecipe(
            **{**recipe_to_payload(configured_embedding_recipe()), "model": "another-model"}
        )
        second = self._second_generation(other_space)

        with mock.patch("kitsune.retrieval.sync.get_embeddings", wraps=get_embeddings) as embed:
            report = sync_document_batch(self.ids)

        self.assertEqual(report.embedding_calls, 1)
        self.assertEqual(embed.call_args.kwargs["recipe"], other_space)
        for document in self.documents:
            with self.subTest(document=document.slug):
                self._assert_embeds(document, other_space, second)


class BulkTaskTests(SimpleTestCase):
    def test_the_task_contract_and_bulk_route_are_stable(self):
        self.assertEqual(sync_documents.name, "kitsune.retrieval.tasks.sync_documents")
        self.assertEqual(app.conf.task_routes[sync_documents.name], {"queue": "retrieval_bulk"})
        self.assertEqual(
            sync_documents.soft_time_limit, settings.RETRIEVAL_TASK_SOFT_TIME_LIMIT_SECONDS
        )
        self.assertEqual(sync_documents.time_limit, settings.RETRIEVAL_TASK_TIME_LIMIT_SECONDS)
        self.assertTrue(sync_documents.ignore_result)
        self.assertNotIn(DocumentLockUnavailable, sync_documents.autoretry_for)
        self.assertIn(DocumentLockBackendError, sync_documents.autoretry_for)

    @override_settings(RETRIEVAL_LIVE_INDEXING=False)
    def test_explicit_bulk_work_runs_with_live_indexing_off_and_preserves_its_target(self):
        with mock.patch(
            "kitsune.retrieval.tasks.sync_document_batch", return_value=BatchSyncReport()
        ) as core:
            sync_documents([2, 1], target_index="chunks-n-plus-one")
        core.assert_called_once_with([2, 1], target_index="chunks-n-plus-one")

    @override_settings(RETRIEVAL_LIVE_INDEXING=False, RETRIEVAL_BULK_MAX_DOCUMENTS=2)
    def test_enqueueing_splits_bounded_payloads_and_preserves_the_target(self):
        with mock.patch.object(sync_documents, "delay") as delay:
            enqueue_document_batch([5, 4, 3, 2, 1], target_index="chunks-n-plus-one")

        self.assertEqual(
            delay.call_args_list,
            [
                mock.call([1, 2], target_index="chunks-n-plus-one"),
                mock.call([3, 4], target_index="chunks-n-plus-one"),
                mock.call([5], target_index="chunks-n-plus-one"),
            ],
        )

    def test_deferred_and_contended_documents_are_requeued_separately(self):
        report = BatchSyncReport(reports={1: mock.Mock()}, contended=(2,), deferred=(3,))
        with (
            mock.patch("kitsune.retrieval.tasks.sync_document_batch", return_value=report),
            mock.patch("kitsune.retrieval.tasks.enqueue_document_batch") as enqueue,
            mock.patch.object(sync_documents, "apply_async") as requeue,
        ):
            sync_documents([1, 2, 3], target_index="chunks-n-plus-one")

        enqueue.assert_called_once_with((3,), target_index="chunks-n-plus-one")
        requeue.assert_called_once()
        self.assertEqual(requeue.call_args.kwargs["args"], [[2]])
        self.assertEqual(
            requeue.call_args.kwargs["kwargs"],
            {"target_index": "chunks-n-plus-one", "contention_attempt": 1},
        )
        self.assertGreater(requeue.call_args.kwargs["countdown"], 0)

    def test_unbroken_contention_stops_requeueing_and_says_so(self):
        report = BatchSyncReport(contended=(2,))
        with (
            mock.patch("kitsune.retrieval.tasks.sync_document_batch", return_value=report),
            mock.patch.object(sync_documents, "apply_async") as requeue,
            self.assertLogs("k.retrieval", level="WARNING") as logs,
        ):
            sync_documents([2], contention_attempt=sync_documents.max_retries)

        requeue.assert_not_called()
        self.assertEqual(logs.records[0].getMessage(), "retrieval.batch.abandoned")

    def test_a_finished_batch_is_not_requeued(self):
        with (
            mock.patch(
                "kitsune.retrieval.tasks.sync_document_batch",
                return_value=BatchSyncReport(reports={1: mock.Mock()}),
            ),
            mock.patch.object(sync_documents, "apply_async") as requeue,
        ):
            sync_documents([1])

        requeue.assert_not_called()
