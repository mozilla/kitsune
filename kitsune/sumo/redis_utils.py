from django.conf import settings
from django.core.cache.backends.base import InvalidCacheBackendError
from django.utils.six.moves.urllib.parse import parse_qsl

from redis import Redis, ConnectionError


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
        host=host, port=port, db=db, password=password, socket_timeout=socket_timeout
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
