from functools import cached_property
from urllib.parse import parse_qsl
from typing import Optional
import math
import random
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
    Reservation-based rate-limiting class that uses Redis.

    A rate limit is a maximum number of calls within a period of time.
    If we divide that period of time by the maximum number of calls, we
    get the amount of time during which at most one call should ever be
    made. If that minimum chunk of time per call is maintained, the rate
    limit will never be exceeded. One or more of these chunks of time can
    be reserved by providing the number of intended calls, and once that
    time is reserved, all other requests to reserve time will be rejected
    until that time expires.

    For example, assuming a rate limit of 100 calls/sec, reserving a single
    call means reserving the next 0.01 seconds (one second divided by 100
    calls) to make that call. Any subsequent reservation request made before
    that 0.01 seconds has expired would be rejected and have to wait. If we
    successfully reserved 50 calls, we would own the next 0.5 seconds
    (50 x 0.01) to make those 50 calls. Again, any subsequent reservation
    request made before that 0.5 seconds has expired would be rejected and
    have to wait.
    """

    ALLOWED_PERIODS = dict(sec=1, min=60, hour=3600, day=86400)

    def __init__(
        self,
        key: str,
        rate: str,
    ):
        self.key = key
        max_calls_str, period_str = rate.replace("/", " ").split()
        max_calls = int(max_calls_str)
        period = self.ALLOWED_PERIODS[period_str]  # seconds
        self.max_num_calls_allowed_per_reservation = max_calls
        # Set the number of milliseconds that will be reserved per call.
        self.reservation_per_call_ms = math.ceil((period / max_calls) * 1000)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

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

    def get_wait_time(self, jitter: float = 0.2) -> float:
        """
        Return a jittered time (in seconds) to wait before attempting another reservation.
        """
        ttl_ms = self.redis.pttl(self.key)
        # Add 10% extra (to be safe) plus some random jitter if requested.
        return 0.0 if ttl_ms < 0 else ((ttl_ms / 1000) * random.uniform(1.1, 1.1 + jitter))

    def reserve(self, num_calls: int = 1) -> float:
        """
        Attempt to reserve the given number of calls. Returns True if the
        reservation was successful or the redis connection is unavailable,
        otherwise False.
        """
        if num_calls > self.max_num_calls_allowed_per_reservation:
            raise ValueError(f"Unable to reserve more calls than allowed ({num_calls})")

        if not self.redis:
            return True

        requested_reservation_ms = num_calls * self.reservation_per_call_ms

        # The expiration of this key is what's important, not its value. Using
        # "num_calls" as its value could prove useful, but it's not necessary.
        return bool(
            self.redis.set(
                self.key,
                str(num_calls),
                nx=True,
                px=requested_reservation_ms,
            )
        )

    def wait_until_reserved(
        self, num_calls: int = 1, jitter: float = 0.2, wait_limit: Optional[float] = None
    ) -> float:
        """
        Wait until we've successfully reserved the given number of calls. Waits
        either indefinitely, if the "wait_limit" is None, or until the "wait_limit"
        has been reached. Uses the given "jitter" factor to randomly vary the wait
        time. Returns the time spent waiting in seconds.
        """
        waited = 0.0
        while not self.reserve(num_calls=num_calls):
            if (wait_limit is not None) and (waited >= wait_limit):
                break
            wait_time = self.get_wait_time(jitter=jitter)
            if wait_time:
                time.sleep(wait_time)
                waited += wait_time

        return waited
