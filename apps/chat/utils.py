import logging

from bleach import clean

from sumo.utils import redis_client


log = logging.getLogger('k.run_chat')


def redis():
    """Return a connection to the appropriate redis server for chat."""
    return redis_client('chat')


def nonce_key(nonce):
    """Return the redis key for storing the nonce-to-user-ID mapping."""
    return 'chatnonce:{n}'.format(n=nonce)


class Safe(object):
    """Wrapper that declares a string to not need HTML-scrubbing before JSON
    encoding"""
    # Think about writing a custom JSONEncoder subclass someday. I found it
    # unacceptably painful, though.
    def __init__(self, string):
        self._inner_string = string

    @classmethod
    def escape(cls, obj):
        """HTML-escape an object unless it's wrapped in Safe().

        Turn Safe instances into strings so JSON encoder doesn't trip on them.

        """
        if isinstance(obj, basestring):
            return clean(obj, tags=[])
        elif isinstance(obj, cls):
            return obj._inner_string
        return obj
