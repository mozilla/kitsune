import multiprocessing
import time
from unittest import mock

from kitsune.sumo.redis_utils import RateLimit, RedisError
from kitsune.sumo.tests import TestCase


class TestRateLimit(TestCase):

    def setUp(self):
        self.key = "test-key"
        self.max_calls = 5
        self.wait_period = 0.1
        self.max_wait_period = 2
        self.rate_limit = RateLimit(
            key=self.key,
            rate=f"{self.max_calls}/sec",
            wait_period=self.wait_period,
            max_wait_period=self.max_wait_period,
        )
        self.rate_limit.redis.delete(self.key)

    def tearDown(self):
        self.rate_limit.close()

    def test_is_rate_limited(self):
        """Ensure basic operation of is_rate_limited()."""
        for i in range(self.max_calls):
            self.assertFalse(self.rate_limit.is_rate_limited(), f"is_rate_limited() call: {i+1}")

        self.assertTrue(self.rate_limit.is_rate_limited())

    def test_is_rate_limited_expiration(self):
        """Ensure is_rate_limited() resets after the expiration period."""
        for i in range(self.max_calls):
            self.assertFalse(self.rate_limit.is_rate_limited(), f"is_rate_limited() call: {i+1}")

        self.assertTrue(self.rate_limit.is_rate_limited())
        time.sleep(1)
        self.assertFalse(self.rate_limit.is_rate_limited())

    def test_wait(self):
        """Ensure wait() waits until we're no longer rate limited."""
        for i in range(self.max_calls):
            self.assertFalse(self.rate_limit.is_rate_limited(), f"is_rate_limited() call: {i+1}")

        time_waited = self.rate_limit.wait()

        self.assertFalse(self.rate_limit.is_rate_limited())
        self.assertTrue(time_waited >= self.wait_period)
        self.assertTrue(time_waited < self.max_wait_period)

    def test_wait_respects_max_wait_period(self):
        """Ensure wait() respects the "max_wait_period" setting."""
        self.rate_limit = RateLimit(
            key=self.key, rate="1/sec", wait_period=0.05, max_wait_period=0.1
        )
        self.assertFalse(self.rate_limit.is_rate_limited())
        time_waited = self.rate_limit.wait()
        # We stopped waiting only because we hit the maximum waiting period.
        self.assertTrue(self.rate_limit.is_rate_limited())
        self.assertTrue(time_waited == 0.1)

    def test_is_rate_limited_multiple_processes(self):
        """Test is_rate_limited() across multiple processes."""
        shared_counter = multiprocessing.Value("i", 0)
        # Create a lock to ensure safe increments of the shared counter.
        shared_counter_lock = multiprocessing.Lock()

        def rate_limited_task():
            """Worker function for multi-process testing."""
            rate_limit = RateLimit(
                key="test-key", rate="5/sec", wait_period=0.1, max_wait_period=2
            )
            if not rate_limit.is_rate_limited():
                with shared_counter_lock:
                    shared_counter.value += 1

        processes = [multiprocessing.Process(target=rate_limited_task) for _ in range(10)]

        for p in processes:
            p.start()

        # Wait until all of the processes have completed.
        for p in processes:
            p.join()

        self.assertEqual(shared_counter.value, 5)

    @mock.patch("kitsune.sumo.redis_utils.redis_client")
    @mock.patch("kitsune.sumo.redis_utils.capture_exception")
    def test_redis_client_failure(self, capture_mock, redis_mock):
        """Ensure that RateLimit handles Redis failures gracefully."""
        redis_mock.side_effect = RedisError()

        self.rate_limit = RateLimit(
            key=self.key, rate="1/min", wait_period=0.05, max_wait_period=0.1
        )

        # If the creation of the redis client failed, there should be no rate limiting.
        self.assertFalse(self.rate_limit.is_rate_limited())
        self.assertFalse(self.rate_limit.is_rate_limited())
        self.assertFalse(self.rate_limit.is_rate_limited())

        redis_mock.assert_called_once()
        capture_mock.assert_called_once_with(redis_mock.side_effect)
