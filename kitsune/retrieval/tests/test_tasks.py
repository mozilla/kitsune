from unittest import mock

from celery.exceptions import Retry
from django.apps import apps
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.test import SimpleTestCase, override_settings
from elastic_transport import ConnectionError as ElasticsearchConnectionError
from elastic_transport import ConnectionTimeout as ElasticsearchConnectionTimeout

from kitsune.retrieval.checks import task_timing_problems
from kitsune.retrieval.index import ChunkIdentity, IndexWriteError
from kitsune.retrieval.locks import DocumentLockBackendError, DocumentLockUnavailable
from kitsune.retrieval.tasks import delete_document, sync_document


class TaskTimingTests(SimpleTestCase):
    """A lease cannot lapse mid-work only if a task cannot outlive it."""

    def test_the_shipped_defaults_satisfy_the_ordering(self):
        self.assertEqual(task_timing_problems(), [])

    def test_each_inversion_is_reported(self):
        inversions = (
            # a request that can outlast the soft limit
            {"RETRIEVAL_EMBEDDING_TIMEOUT_SECONDS": 500},
            # a soft limit at or past the hard limit leaves no room to wind down
            {"RETRIEVAL_TASK_SOFT_TIME_LIMIT_SECONDS": 240},
            # a task allowed to outlive its lease is the whole failure this prevents
            {"RETRIEVAL_TASK_TIME_LIMIT_SECONDS": 300},
        )
        for overrides in inversions:
            with self.subTest(overrides=overrides), override_settings(**overrides):
                self.assertNotEqual(task_timing_problems(), [])

    def test_invalid_limits_are_reported_before_comparing_them(self):
        invalid = (
            {"RETRIEVAL_EMBEDDING_TIMEOUT_SECONDS": 0.0001},
            {"RETRIEVAL_TASK_SOFT_TIME_LIMIT_SECONDS": -1},
            {"RETRIEVAL_TASK_TIME_LIMIT_SECONDS": float("nan")},
            {"RETRIEVAL_LOCK_TTL_SECONDS": True},
        )
        for overrides in invalid:
            with self.subTest(overrides=overrides), override_settings(**overrides):
                self.assertNotEqual(task_timing_problems(), [])

    def test_app_startup_refuses_an_inverted_configuration(self):
        config = apps.get_app_config("retrieval")
        with (
            override_settings(RETRIEVAL_TASK_TIME_LIMIT_SECONDS=9_000),
            self.assertRaises(ImproperlyConfigured),
        ):
            config.ready()

    def test_the_tasks_use_the_retrieval_limits_and_not_global_ones(self):
        for task in (sync_document, delete_document):
            with self.subTest(task=task.name):
                self.assertEqual(
                    task.soft_time_limit, settings.RETRIEVAL_TASK_SOFT_TIME_LIMIT_SECONDS
                )
                self.assertEqual(task.time_limit, settings.RETRIEVAL_TASK_TIME_LIMIT_SECONDS)
                self.assertTrue(task.ignore_result)

    def test_no_global_celery_time_limit_is_imposed(self):
        # A global limit would truncate unrelated Kitsune tasks.
        self.assertIsNone(getattr(settings, "CELERY_TASK_TIME_LIMIT", None))
        self.assertIsNone(getattr(settings, "CELERY_TASK_SOFT_TIME_LIMIT", None))


class TaskRoutingTests(SimpleTestCase):
    def test_both_tasks_are_routed_to_the_retrieval_queue(self):
        from kitsune.celery import app

        for name in (sync_document.name, delete_document.name):
            with self.subTest(task=name):
                self.assertEqual(app.conf.task_routes[name], {"queue": "retrieval"})

    def test_the_task_names_are_stable(self):
        self.assertEqual(sync_document.name, "kitsune.retrieval.tasks.sync_document")
        self.assertEqual(delete_document.name, "kitsune.retrieval.tasks.delete_document")


@override_settings(RETRIEVAL_LIVE_INDEXING=True)
class TaskBehaviourTests(SimpleTestCase):
    def setUp(self):
        self.identity = ChunkIdentity("kb", "42", "en-US")

    def test_sync_delegates_to_the_sync_core(self):
        with mock.patch("kitsune.retrieval.tasks.sync_document_chunks") as core:
            sync_document(42)
        core.assert_called_once_with(42)

    def test_delete_takes_json_safe_arguments_and_rebuilds_the_identity(self):
        with mock.patch("kitsune.retrieval.tasks.delete_document_chunks") as core:
            delete_document("kb", "42", "en-US")
        core.assert_called_once_with(self.identity, target_index=None)

    def test_delete_evicts_only_the_pinned_index_when_reconciliation_names_one(self):
        # Reconciling one generation must not empty the other.
        with mock.patch("kitsune.retrieval.tasks.delete_document_chunks") as core:
            delete_document("kb", "42", "en-US", target_index="chunks_n_plus_one")
        core.assert_called_once_with(self.identity, target_index="chunks_n_plus_one")

    def test_transient_and_replayable_errors_are_retried(self):
        errors = (
            DocumentLockUnavailable("held"),
            DocumentLockBackendError("down"),
            IndexWriteError("partial write"),
            ElasticsearchConnectionError("unavailable"),
            ElasticsearchConnectionTimeout("timed out"),
        )
        for error in errors:
            with self.subTest(error=type(error).__name__):
                with (
                    mock.patch("kitsune.retrieval.tasks.sync_document_chunks", side_effect=error),
                    mock.patch.object(sync_document, "retry", side_effect=Retry) as retry,
                    self.assertRaises(Retry),
                ):
                    sync_document(42)
                retry.assert_called_once()

    def test_a_permanent_error_is_not_retried(self):
        with (
            mock.patch(
                "kitsune.retrieval.tasks.sync_document_chunks",
                side_effect=ImproperlyConfigured("no backend"),
            ),
            mock.patch.object(sync_document, "retry") as retry,
            self.assertRaises(ImproperlyConfigured),
        ):
            sync_document(42)
        retry.assert_not_called()

    def test_live_indexing_off_skips_the_work_entirely(self):
        with (
            override_settings(RETRIEVAL_LIVE_INDEXING=False),
            mock.patch("kitsune.retrieval.tasks.sync_document_chunks") as core,
        ):
            sync_document(42)
        core.assert_not_called()

    def test_deletion_runs_even_when_live_indexing_is_off(self):
        # Removing content that should no longer be served is not a freshness optimization.
        with (
            override_settings(RETRIEVAL_LIVE_INDEXING=False),
            mock.patch("kitsune.retrieval.tasks.delete_document_chunks") as core,
        ):
            delete_document("kb", "42", "en-US")
        core.assert_called_once()
