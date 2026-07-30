import time
from unittest import mock
from uuid import uuid4

from django.core.exceptions import ImproperlyConfigured
from django.test import SimpleTestCase, override_settings
from redis.exceptions import ConnectionError as RedisConnectionError

from kitsune.retrieval.index import ChunkIdentity
from kitsune.retrieval.locks import (
    DocumentLockBackendError,
    DocumentLockUnavailable,
    document_lock,
    document_lock_key,
    redis_lease,
)
from kitsune.sumo.redis_utils import RedisError, redis_client


class LeaseTestCase(SimpleTestCase):
    def setUp(self):
        super().setUp()
        self.client = redis_client("default")
        self.key = f"retrieval:test-lease:{uuid4().hex}"
        self.addCleanup(self.client.delete, self.key)

    def steal(self):
        """Simulate a successor taking the key over after the holder's lease expired."""
        successor = f"successor-{uuid4().hex}"
        self.client.set(self.key, successor, px=60_000)
        return successor

    def broken_backend(self, lease):
        """Make every token-checked Redis call on this lease fail."""
        broken = mock.Mock()
        for call in (broken.owned, broken.reacquire, broken.release):
            call.side_effect = RedisConnectionError("connection lost")
        return mock.patch.object(lease, "_lock", broken)


class AcquireAndReleaseTests(LeaseTestCase):
    def test_holds_the_key_with_a_ttl_and_frees_it_on_exit(self):
        with redis_lease(self.key) as lease:
            self.assertTrue(lease.owns_lease())
            self.assertEqual(self.client.get(self.key), lease.token)
            self.assertGreater(self.client.pttl(self.key), 0)

        self.assertIsNone(self.client.get(self.key))

    def test_a_second_holder_is_refused_while_the_lease_is_held(self):
        with redis_lease(self.key):
            with self.assertRaises(DocumentLockUnavailable):
                with redis_lease(self.key):
                    pass

    def test_the_key_is_reacquirable_once_released(self):
        with redis_lease(self.key) as first:
            first_token = first.token
        with redis_lease(self.key) as second:
            self.assertNotEqual(second.token, first_token)

    def test_an_exception_in_the_body_still_releases_the_lease(self):
        with self.assertRaises(ValueError):
            with redis_lease(self.key):
                raise ValueError("boom")
        self.assertIsNone(self.client.get(self.key))


@override_settings(RETRIEVAL_LOCK_TTL_SECONDS=60, RETRIEVAL_LOCK_HEARTBEAT_SECONDS=30)
class RenewalAndOwnershipTests(LeaseTestCase):
    def test_renew_extends_the_expiry(self):
        with redis_lease(self.key, ttl_seconds=3) as lease:
            time.sleep(0.5)
            shortened = self.client.pttl(self.key)
            lease.renew()
            self.assertGreater(self.client.pttl(self.key), shortened)

    def test_a_stolen_lease_is_no_longer_owned(self):
        with redis_lease(self.key) as lease:
            self.steal()
            self.assertFalse(lease.owns_lease())

    def test_renewing_a_stolen_lease_raises(self):
        with redis_lease(self.key) as lease:
            self.steal()
            with self.assertRaises(DocumentLockUnavailable):
                lease.renew()

    def test_release_never_deletes_a_successors_lease(self):
        with redis_lease(self.key) as lease:
            successor = self.steal()
            lease.release()
            self.assertEqual(self.client.get(self.key), successor)

        # Leaving the context must not delete it either.
        self.assertEqual(self.client.get(self.key), successor)

    def test_renewing_an_expired_lease_does_not_recreate_it(self):
        with redis_lease(self.key) as lease:
            self.client.delete(self.key)  # stand-in for the ttl elapsing
            with self.assertRaises(DocumentLockUnavailable):
                lease.renew()
            # A renew that re-created the key would hand a second worker the same lease.
            self.assertIsNone(self.client.get(self.key))


class HeartbeatTests(LeaseTestCase):
    def test_heartbeat_keeps_a_lease_alive_across_a_blocking_call(self):
        # The blocking call outlasts the ttl several times over: without renewal from a
        # background heartbeat the key would be gone before it returns.
        with redis_lease(self.key, ttl_seconds=0.3, heartbeat_seconds=0.1) as lease:
            time.sleep(0.9)
            self.assertTrue(lease.owns_lease())
            self.assertEqual(self.client.get(self.key), lease.token)

        self.assertIsNone(self.client.get(self.key))

    def test_the_heartbeat_thread_stops_when_the_lease_is_released(self):
        with redis_lease(self.key, ttl_seconds=0.3, heartbeat_seconds=0.1) as lease:
            time.sleep(0.2)
            self.assertTrue(lease.heartbeat_running)
            lease.release()
            self.assertFalse(lease.heartbeat_running)

    def test_the_heartbeat_stops_renewing_once_the_lease_is_stolen(self):
        with redis_lease(self.key, ttl_seconds=0.3, heartbeat_seconds=0.1) as lease:
            successor = self.steal()
            time.sleep(0.3)
            self.assertFalse(lease.owns_lease())
            self.assertEqual(self.client.get(self.key), successor)


class BackendFailureTests(LeaseTestCase):
    def test_an_unreachable_backend_fails_closed_on_acquire(self):
        for error in (RedisError("no redis"), RedisConnectionError("connection lost")):
            with (
                self.subTest(error=error),
                mock.patch("kitsune.retrieval.locks._lock_client", side_effect=error),
                self.assertRaises(DocumentLockBackendError),
            ):
                with redis_lease(self.key):
                    pass

    def test_a_failing_acquire_fails_closed(self):
        client = mock.Mock()
        client.lock.return_value.acquire.side_effect = RedisConnectionError("connection lost")
        with (
            mock.patch("kitsune.retrieval.locks._lock_client", return_value=client),
            self.assertRaises(DocumentLockBackendError),
        ):
            with redis_lease(self.key):
                pass

    def test_a_failing_renew_fails_closed(self):
        with redis_lease(self.key, heartbeat_seconds=10) as lease:
            with self.broken_backend(lease), self.assertRaises(DocumentLockBackendError):
                lease.renew()

    def test_a_failing_release_surfaces_the_backend_error(self):
        with redis_lease(self.key, heartbeat_seconds=10) as lease:
            with self.broken_backend(lease), self.assertRaises(DocumentLockBackendError):
                lease.release()

    def test_ownership_cannot_be_confirmed_when_the_backend_fails(self):
        with redis_lease(self.key, heartbeat_seconds=10) as lease:
            with (
                mock.patch.object(
                    lease._lock, "owned", side_effect=RedisConnectionError("connection lost")
                ),
                self.assertRaises(DocumentLockBackendError),
            ):
                lease.owns_lease()

    def test_release_cleans_up_after_a_transient_ownership_check_failure(self):
        with redis_lease(self.key, heartbeat_seconds=10) as lease:
            with (
                mock.patch.object(
                    lease._lock, "owned", side_effect=RedisConnectionError("connection lost")
                ),
                self.assertRaises(DocumentLockBackendError),
            ):
                lease.owns_lease()

            lease.release()
            self.assertIsNone(self.client.get(self.key))

    def test_a_backend_failure_during_the_heartbeat_remains_retryable(self):
        with redis_lease(self.key, ttl_seconds=0.4, heartbeat_seconds=0.1) as lease:
            with self.broken_backend(lease):
                time.sleep(0.3)
            # The background thread cannot raise into this thread. Preserve why ownership
            # was surrendered so the sync caller still sees a retryable backend failure.
            with self.assertRaises(DocumentLockBackendError):
                lease.owns_lease()


class DocumentLockTests(LeaseTestCase):
    def setUp(self):
        super().setUp()
        self.identity = ChunkIdentity("kb", uuid4().hex, "en-US")
        self.addCleanup(self.client.delete, document_lock_key(self.identity))

    def test_the_key_is_namespaced_and_derived_from_the_identity(self):
        key = document_lock_key(self.identity)
        self.assertTrue(key.startswith("retrieval:"))
        self.assertIn(self.identity.object_id, key)
        self.assertIn("en-US", key)

    def test_one_document_cannot_be_locked_twice(self):
        with document_lock(self.identity):
            with self.assertRaises(DocumentLockUnavailable):
                with document_lock(self.identity):
                    pass

    def test_different_documents_do_not_contend(self):
        other = ChunkIdentity("kb", uuid4().hex, "en-US")
        self.addCleanup(self.client.delete, document_lock_key(other))
        with document_lock(self.identity), document_lock(other) as second:
            self.assertTrue(second.owns_lease())

    def test_the_same_object_in_another_locale_does_not_contend(self):
        translation = ChunkIdentity("kb", self.identity.object_id, "de")
        self.addCleanup(self.client.delete, document_lock_key(translation))
        with document_lock(self.identity), document_lock(translation) as second:
            self.assertTrue(second.owns_lease())


class LockSettingsTests(LeaseTestCase):
    def test_invalid_or_unscoped_keys_are_rejected(self):
        for key in (None, "", "shared-lock", "retrieval:", "retrieval:   "):
            with self.subTest(key=key), self.assertRaises(ValueError):
                with redis_lease(key):
                    pass

    def test_invalid_intervals_fail_closed(self):
        invalid = (
            {"RETRIEVAL_LOCK_TTL_SECONDS": 0},
            {"RETRIEVAL_LOCK_TTL_SECONDS": -1},
            {"RETRIEVAL_LOCK_TTL_SECONDS": True},
            {"RETRIEVAL_LOCK_TTL_SECONDS": "60"},
            {"RETRIEVAL_LOCK_HEARTBEAT_SECONDS": 0},
            {"RETRIEVAL_LOCK_HEARTBEAT_SECONDS": -1},
            {"RETRIEVAL_LOCK_HEARTBEAT_SECONDS": True},
            # A heartbeat at or beyond the ttl can never renew in time.
            {"RETRIEVAL_LOCK_TTL_SECONDS": 10, "RETRIEVAL_LOCK_HEARTBEAT_SECONDS": 10},
            {"RETRIEVAL_LOCK_TTL_SECONDS": 10, "RETRIEVAL_LOCK_HEARTBEAT_SECONDS": 30},
        )
        for overrides in invalid:
            with (
                self.subTest(overrides=overrides),
                override_settings(**overrides),
                self.assertRaises(ImproperlyConfigured),
            ):
                with redis_lease(self.key):
                    pass
        self.assertIsNone(self.client.get(self.key))

    def test_invalid_arguments_fail_closed_without_acquiring(self):
        for kwargs in (
            {"ttl_seconds": 0},
            {"heartbeat_seconds": 0},
            {"ttl_seconds": 0.0001},
            {"ttl_seconds": 0.001},
            {"heartbeat_seconds": 0.0001},
            {"ttl_seconds": "5"},
        ):
            with (
                self.subTest(kwargs=kwargs),
                self.assertRaises(ImproperlyConfigured),
            ):
                with redis_lease(self.key, **kwargs):
                    pass
        self.assertIsNone(self.client.get(self.key))
