from functools import cached_property
from urllib.parse import parse_qsl
import time

from django.conf import settings
from django.core.cache.backends.base import InvalidCacheBackendError
from redis import ConnectionError, Redis
from sentry_sdk import capture_exception


class RedisError(Exception):
    """An error with the redis configuration or connnection."""


def redis_client(name):
    """Get a Redis client.

    Uses the name argument to lookup the connection string in the
    settings.REDIS_BACKEND dict.
    """
    if name not in settings.REDIS_BACKENDS:
        raise RedisError("{k} is not defined in settings.REDIS_BACKENDS".format(k=name))

    uri = settings.REDIS_BACKENDS[name]
    _, server, params = parse_backend_uri(uri)
    db = params.pop("db", 1)

    try:
        db = int(db)
    except (ValueError, TypeError):
        db = 1
    try:
        socket_timeout = float(params.pop("socket_timeout"))
    except (KeyError, ValueError):
        socket_timeout = None
    password = params.pop("password", None)
    if ":" in server:
        host, port = server.split(":")
        try:
            port = int(port)
        except (ValueError, TypeError):
            port = 6379
    else:
        host = server
        port = 6379
    redis = Redis(
        host=host,
        port=port,
        db=db,
        password=password,
        socket_timeout=socket_timeout,
        decode_responses=True,
    )
    try:
        # Make a cheap call to verify we can connect.
        redis.exists("dummy-key")
    except ConnectionError:
        raise RedisError("Unable to connect to redis backend: {k}".format(k=name))
    return redis


# Copy/pasted from django 1.6:
# https://github.com/django/django/blob/9d915ac1be1e7b8cfea3c92f707a4aeff4e62583/django/core/cache/__init__.py
def parse_backend_uri(backend_uri):
    """
    Converts the "backend_uri" into a cache scheme ('db', 'memcached', etc), a
    host and any extra params that are required for the backend. Returns a
    (scheme, host, params) tuple.
    """
    if backend_uri.find(":") == -1:
        raise InvalidCacheBackendError(
            "Backend URI must start with scheme://. URI: {}".format(backend_uri)
        )

    scheme, rest = backend_uri.split(":", 1)

    if not rest.startswith("//"):
        raise InvalidCacheBackendError(
            "Backend URI must start with scheme://. Split URI: {}".format(backend_uri)
        )

    host = rest[2:]
    qpos = rest.find("?")
    if qpos != -1:
        params = dict(parse_qsl(rest[qpos + 1 :]))
        host = rest[2:qpos]
    else:
        params = {}
    if host.endswith("/"):
        host = host[:-1]

    return scheme, host, params


class RateLimit:
    """
    Simple multi-process rate limiting class that uses Redis.
    """

    ALLOWED_PERIODS = dict(sec=1, min=60, hour=3600, day=86400)

    def __init__(
        self, key: str, rate: str, wait_period: int | float, max_wait_period: int | float
    ):
        self.key = key
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
            time.sleep(self.wait_period)
            waited += self.wait_period
            if self.max_wait_period and (waited >= self.max_wait_period):
                break
        return waited
