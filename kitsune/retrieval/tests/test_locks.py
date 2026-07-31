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
        for call in (broken.reacquire, broken.release):
            call.side_effect = RedisConnectionError("connection lost")
        return mock.patch.object(lease, "_lock", broken)


class AcquireAndReleaseTests(LeaseTestCase):
    def test_holds_the_key_with_a_ttl_and_frees_it_on_exit(self):
        with redis_lease(self.key) as lease:
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

    def test_releasing_twice_is_harmless(self):
        # Lock.release() clears its own token first, so an unguarded second call would
        # complain about an unlocked lock.
        with redis_lease(self.key) as lease:
            lease.release()
            lease.release()
        self.assertIsNone(self.client.get(self.key))


class RenewalTests(LeaseTestCase):
    def test_renew_extends_the_expiry(self):
        with redis_lease(self.key, ttl_seconds=3) as lease:
            time.sleep(0.5)
            shortened = self.client.pttl(self.key)
            lease.renew()
            self.assertGreater(self.client.pttl(self.key), shortened)

    def test_renewing_a_stolen_lease_raises(self):
        with redis_lease(self.key) as lease:
            successor = self.steal()
            with self.assertRaises(DocumentLockUnavailable):
                lease.renew()
            self.assertEqual(self.client.get(self.key), successor)

    def test_renewing_an_expired_lease_does_not_recreate_it(self):
        with redis_lease(self.key) as lease:
            self.client.delete(self.key)  # stand-in for the ttl elapsing
            with self.assertRaises(DocumentLockUnavailable):
                lease.renew()
            # A renew that re-created the key would hand a second worker the same lease.
            self.assertIsNone(self.client.get(self.key))

    def test_release_never_deletes_a_successors_lease(self):
        with redis_lease(self.key) as lease:
            successor = self.steal()
            lease.release()
            self.assertEqual(self.client.get(self.key), successor)

        # Leaving the context must not delete it either.
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
        with redis_lease(self.key) as lease:
            with self.broken_backend(lease), self.assertRaises(DocumentLockBackendError):
                lease.renew()

    def test_a_failing_release_surfaces_the_backend_error(self):
        with redis_lease(self.key) as lease:
            with self.broken_backend(lease), self.assertRaises(DocumentLockBackendError):
                lease.release()

    def test_context_cleanup_ignores_a_release_failure(self):
        with redis_lease(self.key) as lease:
            broken = self.broken_backend(lease)
            broken.start()
            self.addCleanup(broken.stop)
        # The protected work finished; the ttl provides cleanup without retrying that work.
        self.assertGreater(self.client.pttl(self.key), 0)


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
            self.assertEqual(self.client.get(document_lock_key(other)), second.token)

    def test_the_same_object_in_another_locale_does_not_contend(self):
        translation = ChunkIdentity("kb", self.identity.object_id, "de")
        self.addCleanup(self.client.delete, document_lock_key(translation))
        with document_lock(self.identity), document_lock(translation) as second:
            self.assertEqual(self.client.get(document_lock_key(translation)), second.token)


class LockSettingsTests(LeaseTestCase):
    def test_invalid_or_unscoped_keys_are_rejected(self):
        for key in (None, "", "shared-lock", "retrieval:", "retrieval:   "):
            with self.subTest(key=key), self.assertRaises(ValueError):
                with redis_lease(key):
                    pass

    def test_an_invalid_configured_ttl_fails_closed(self):
        for ttl in (0, -1, True, "60", float("inf"), float("nan")):
            with (
                self.subTest(ttl=ttl),
                override_settings(RETRIEVAL_LOCK_TTL_SECONDS=ttl),
                self.assertRaises(ImproperlyConfigured),
            ):
                with redis_lease(self.key):
                    pass
        self.assertIsNone(self.client.get(self.key))

    def test_an_invalid_ttl_argument_fails_closed_without_acquiring(self):
        # Below a millisecond the expiry truncates to zero, which would delete the key.
        for ttl in (0, 0.0001, "5", float("nan")):
            with (
                self.subTest(ttl=ttl),
                self.assertRaises(ImproperlyConfigured),
            ):
                with redis_lease(self.key, ttl_seconds=ttl):
                    pass
        self.assertIsNone(self.client.get(self.key))
