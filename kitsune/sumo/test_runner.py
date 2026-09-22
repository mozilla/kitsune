import multiprocessing
import os
from contextlib import closing

# Django also uses this discovery sentinel; unittest's type stubs omit it.
from unittest.loader import _FailedTest  # type: ignore[attr-defined]
from uuid import uuid4

from django.conf import settings
from django.test.runner import DiscoverRunner, ParallelTestSuite, filter_tests_by_tags
from django.test.utils import iter_test_cases, override_settings

from kitsune.search.es_utils import es_client
from kitsune.sumo.redis_utils import redis_client

_TEST_PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

# Django imports the runner before resolving --parallel=auto, which falls back to
# one worker for forkserver. Select spawn before that calculation.
multiprocessing.set_start_method("spawn", force=True)


def _configure_parallel_worker(index_prefix=None, lock_prefix=None):
    """Configure worker isolation before Django imports the document classes."""

    locmem_settings = {
        **settings.CACHES,
        "default": {
            **settings.CACHES["default"],
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "test-worker-default",
        },
    }

    # Spawned workers don't inherit the parent runner's settings override.
    worker_settings = {
        "CACHES": locmem_settings,
        "PASSWORD_HASHERS": _TEST_PASSWORD_HASHERS,
    }
    if index_prefix is not None:
        worker_id = os.getpid()
        worker_settings.update(
            ES_INDEX_PREFIX=f"{index_prefix}_{worker_id}",
            RETRIEVAL_LOCK_KEY_PREFIX=f"{lock_prefix}:{worker_id}",
        )
    override_settings(**worker_settings).enable()


class SpawnParallelTestSuite(ParallelTestSuite):
    process_setup = _configure_parallel_worker

    def run(self, result):
        es_tests = filter_tests_by_tags(iter_test_cases(self), {"es"}, set())
        if not any(not isinstance(test, _FailedTest) for test in es_tests):
            return super().run(result)

        run_id = uuid4().hex
        index_prefix = f"{settings.ES_INDEX_PREFIX}_test_{run_id}"
        lock_prefix = f"{settings.RETRIEVAL_LOCK_KEY_PREFIX}:test:{run_id}"
        self.process_setup_args = (index_prefix, lock_prefix)
        try:
            return super().run(result)
        finally:
            # Failfast can terminate workers before their test teardown runs.
            with closing(es_client()) as client:
                client.indices.delete(index=f"{index_prefix}_*", ignore_unavailable=True)
            with redis_client("default") as client:
                for key in client.scan_iter(match=f"{lock_prefix}:*"):
                    client.delete(key)


class SpawnParallelRunner(DiscoverRunner):
    """
    Test runner with spawned workers and isolated caches, indices, and retrieval leases.

    Spawn avoids inheriting psycopg3 connections from the parent process.
    """

    parallel_test_suite = SpawnParallelTestSuite

    def run_tests(self, test_labels, **kwargs):
        with override_settings(PASSWORD_HASHERS=_TEST_PASSWORD_HASHERS):
            return super().run_tests(test_labels, **kwargs)
