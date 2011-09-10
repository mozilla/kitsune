import logging

from sumo.utils import redis_client


log = logging.getLogger('k.run_chat')


def redis():
    """Return a connection to the appropriate redis server for chat."""
    return redis_client('chat')


def nonce_key(nonce):
    """Return the redis key for storing the nonce-to-user-ID mapping."""
    return 'chatnonce:{n}'.format(n=nonce)
