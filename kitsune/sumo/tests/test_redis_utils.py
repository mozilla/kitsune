import multiprocessing
import time
from unittest import mock

from kitsune.sumo.redis_utils import RateLimit, RedisError
from kitsune.sumo.tests import TestCase


class TestRateLimit(TestCase):

    def setUp(self):
        self.key = "test-key"
        self.max_calls = 10
        self.rate_limit = RateLimit(key=self.key, rate=f"{self.max_calls}/sec")
        self.rate_limit.redis.delete(self.key)

    def tearDown(self):
        self.rate_limit.close()

    def test_attributes(self):
        rl = RateLimit(key="test-1", rate="100/sec")
        self.assertEqual(rl.key, "test-1")
        self.assertEqual(rl.reservation_per_call_ms, 10)
        self.assertEqual(rl.max_num_calls_allowed_per_reservation, 100)

        rl = RateLimit(key="test-2", rate="30/min")
        self.assertEqual(rl.key, "test-2")
        self.assertEqual(rl.reservation_per_call_ms, 2000)
        self.assertEqual(rl.max_num_calls_allowed_per_reservation, 30)

        rl = RateLimit(key="test-3", rate="7200/hour")
        self.assertEqual(rl.reservation_per_call_ms, 500)
        self.assertEqual(rl.max_num_calls_allowed_per_reservation, 7200)

        rl = RateLimit(key="test-4", rate="400/day")
        self.assertEqual(rl.reservation_per_call_ms, 216000)
        self.assertEqual(rl.max_num_calls_allowed_per_reservation, 400)

    def test_reserve(self):
        self.assertTrue(self.rate_limit.reserve(num_calls=5))
        self.assertFalse(self.rate_limit.reserve(num_calls=1))
        wait_time = self.rate_limit.get_wait_time()
        self.assertTrue(wait_time > 0)
        time.sleep(wait_time)
        self.assertTrue(self.rate_limit.reserve(num_calls=10))

    def test_reserve_more_than_allowed(self):
        with self.assertRaises(ValueError):
            self.rate_limit.reserve(num_calls=self.max_calls + 1)

    def test_wait_until_reserved(self):
        waited = self.rate_limit.wait_until_reserved(num_calls=3, jitter=0.0, wait_limit=1)
        self.assertEqual(waited, 0)
        waited = self.rate_limit.wait_until_reserved(num_calls=7, jitter=0.0, wait_limit=1)
        self.assertTrue(waited > 0)
        self.assertFalse(self.rate_limit.reserve(num_calls=3))

    def test_wait_until_reserved_respects_wait_limit(self):
        waited = self.rate_limit.wait_until_reserved(num_calls=5, wait_limit=1)
        self.assertEqual(waited, 0)
        waited = self.rate_limit.wait_until_reserved(num_calls=1, wait_limit=0)
        self.assertEqual(waited, 0)
        self.assertFalse(self.rate_limit.reserve(num_calls=1))

    def test_wait_until_reserved_with_multiple_processes(self):
        shared_counter = multiprocessing.Value("i", 0)

        def func():
            """Worker function for multi-process testing."""
            rate_limit = RateLimit(key="test-key", rate="5/sec")
            if rate_limit.reserve(num_calls=5):
                with shared_counter.get_lock():
                    shared_counter.value += 1

        processes = [multiprocessing.Process(target=func) for _ in range(4)]

        for p in processes:
            p.start()

        # Wait until all of the processes have completed.
        for p in processes:
            p.join()

        # Only one of the processes should have been able to reserve its calls.
        self.assertEqual(shared_counter.value, 1)

    @mock.patch("kitsune.sumo.redis_utils.redis_client")
    @mock.patch("kitsune.sumo.redis_utils.capture_exception")
    def test_redis_client_failure(self, capture_mock, redis_mock):
        """Ensure that RateLimit handles Redis failures gracefully."""
        redis_mock.side_effect = RedisError()

        self.rate_limit = RateLimit(key=self.key, rate="1/min")

        # If the creation of the redis client failed, there should be no rate limiting.
        self.assertTrue(self.rate_limit.reserve(num_calls=1))
        self.assertTrue(self.rate_limit.reserve(num_calls=1))
        self.assertTrue(self.rate_limit.reserve(num_calls=1))

        redis_mock.assert_called_once()
        capture_mock.assert_called_once_with(redis_mock.side_effect)
