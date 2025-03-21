from functools import cached_property
import random
import time

from django.conf import settings
from redis import ConnectionError, Redis
from sentry_sdk import capture_exception


class RedisError(Exception):
    """An error with the redis configuration or connnection."""


def redis_client(name: str) -> Redis:
    """
    Creates a Redis client from the connection URL specified by name, which
    must be provided within settings.REDIS_BACKENDS.
    """
    url = settings.REDIS_BACKENDS.get(name)

    if not url:
        raise RedisError(f"{name} is not defined in settings.REDIS_BACKENDS")

    # The "decode_responses" keyword argument is a default, used only
    # if not provided in the URL.
    redis = Redis.from_url(url, decode_responses=True)

    # Verify that we can connect.
    try:
        redis.exists("dummy-key")
    except ConnectionError:
        raise RedisError(f"Unable to connect to redis backend: {name}")

    return redis


class RateLimit:
    """
    Simple multi-process rate limiting class that uses Redis.
    """

    ALLOWED_PERIODS = dict(sec=1, min=60, hour=3600, day=86400)

    def __init__(
        self,
        key: str,
        rate: str,
        wait_period: int | float,
        max_wait_period: int | float,
        jitter: float = 0.2,
    ):
        self.key = key
        self.jitter = jitter  # percentage
        self.wait_period = wait_period  # seconds
        self.max_wait_period = max_wait_period  # seconds
        max_calls, period = rate.replace("/", " ").split()
        self.max_calls = int(max_calls)
        self.period = self.ALLOWED_PERIODS[period]

    @cached_property
    def redis(self):
        """
        Creates and caches the Redis client on demand.
        """
        try:
            return redis_client("default")
        except RedisError as err:
            capture_exception(err)
        return None

    def close(self):
        """
        Close the Redis client if it exists.
        """
        # We only need to do something if we've cached a Redis client.
        if "redis" in self.__dict__:
            if self.redis:
                try:
                    self.redis.close()
                except Exception as err:
                    capture_exception(err)
            # Remove the cached Redis client.
            delattr(self, "redis")

    def is_rate_limited(self):
        """
        Returns True if the rate limit has been exceeded, False otherwise.
        """
        if not self.redis:
            # If we can't connect to Redis, don't rate limit.
            return False
        # The first caller refreshes the "token bucket" with the maximum number of
        # calls allowed in a period, while this is a "noop" for all other callers.
        # Only the first caller will be able to set the key and its expiration, since
        # the key will only be set if it doesn't already exist (nx=True). Note that
        # once a key expires, it's considered to no longer exist.
        self.redis.set(self.key, self.max_calls, nx=True, ex=self.period)
        # If the "token bucket" is empty, start rate limiting until it's refreshed
        # again after the period expires.
        return self.redis.decrby(self.key, 1) < 0

    def wait(self):
        """
        Wait until we're no longer rate limited. Waits either indefinitely, if
        the "max_wait_period" is None or zero, or until the "max_wait_period"
        has been reached. Returns the time spent waiting in seconds.
        """
        waited = 0
        while self.is_rate_limited():
            jittered_wait = self.wait_period * random.uniform(1 - self.jitter, 1 + self.jitter)
            time.sleep(jittered_wait)
            waited += jittered_wait
            if self.max_wait_period and (waited >= self.max_wait_period):
                break
        return waited
