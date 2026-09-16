import multiprocessing

import django.core.cache as cache_module
from django.conf import settings
from django.core.cache import CacheHandler
from django.test.runner import DiscoverRunner, ParallelTestSuite
from django.test.utils import override_settings

_TEST_PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]


def _configure_parallel_worker():
    """
    Runs inside each parallel worker after startup, before any test.
    Overrides the cache to a local in-memory backend so workers don't
    share Redis — preventing cache.clear() in one worker from wiping
    sessions in another.
    """

    locmem_settings = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        }
    }
    settings.CACHES = locmem_settings
    cache_module.caches = CacheHandler(locmem_settings)

    # Spawned workers don't inherit the parent runner's settings override.
    override_settings(PASSWORD_HASHERS=_TEST_PASSWORD_HASHERS).enable()


class SpawnParallelTestSuite(ParallelTestSuite):
    process_setup = _configure_parallel_worker


class SpawnParallelRunner(DiscoverRunner):
    """
    Test runner that uses multiprocessing 'spawn' instead of 'fork'.
    This avoids psycopg3 connection-inheritance issues with the default
    fork-based parallel runner, and isolates each worker's cache.
    """

    parallel_test_suite = SpawnParallelTestSuite

    def run_tests(self, test_labels, **kwargs):
        if self.parallel > 1:
            multiprocessing.set_start_method("spawn", force=True)
        with override_settings(PASSWORD_HASHERS=_TEST_PASSWORD_HASHERS):
            return super().run_tests(test_labels, **kwargs)
