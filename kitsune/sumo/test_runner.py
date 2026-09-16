import multiprocessing

from django.conf import settings
from django.test.runner import DiscoverRunner, ParallelTestSuite
from django.test.utils import override_settings

_TEST_PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

# Django imports the runner before resolving --parallel=auto, which falls back to
# one worker for forkserver. Select spawn before that calculation.
multiprocessing.set_start_method("spawn", force=True)


def _configure_parallel_worker():
    """
    Runs inside each parallel worker after startup, before any test.
    Gives the default cache a process-local backend so workers cannot clear
    each other's sessions, while preserving the other configured cache aliases.
    """

    locmem_settings = {
        **settings.CACHES,
        "default": {
            **settings.CACHES["default"],
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "test-worker-default",
        },
    }

    # Spawned workers don't inherit the parent runner's settings override.
    override_settings(
        CACHES=locmem_settings,
        PASSWORD_HASHERS=_TEST_PASSWORD_HASHERS,
    ).enable()


class SpawnParallelTestSuite(ParallelTestSuite):
    process_setup = _configure_parallel_worker


class SpawnParallelRunner(DiscoverRunner):
    """
    Test runner with spawned workers and isolated caches.

    Spawn avoids inheriting psycopg3 connections from the parent process.
    """

    parallel_test_suite = SpawnParallelTestSuite

    def run_tests(self, test_labels, **kwargs):
        with override_settings(PASSWORD_HASHERS=_TEST_PASSWORD_HASHERS):
            return super().run_tests(test_labels, **kwargs)
