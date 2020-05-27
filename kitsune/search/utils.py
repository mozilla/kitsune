import time
from itertools import islice

from django.conf import settings

import bleach

from kitsune.lib.sumo_locales import LOCALES


class FakeLogger(object):
    """Fake logger that we can pretend is a Python Logger

    Why? Well, because Django has logging settings that prevent me
    from setting up a logger here that uses the stdout that the Django
    BaseCommand has. At some point p while fiddling with it, I
    figured, 'screw it--I'll just write my own' and did.

    The minor ramification is that this isn't a complete
    implementation so if it's missing stuff, we'll have to add it.
    """

    def __init__(self, stdout):
        self.stdout = stdout

    def _out(self, level, msg, *args):
        msg = msg % args
        self.stdout.write('%s %-8s: %s\n' % (
                          time.strftime('%H:%M:%S'), level, msg))

    def info(self, msg, *args):
        self._out('INFO', msg, *args)

    def error(self, msg, *args):
        self._out('ERROR', msg, *args)


def clean_excerpt(excerpt):
    return bleach.clean(excerpt, tags=['b', 'i'])


def locale_or_default(locale):
    """Return `locale` or, if `locale` isn't a known locale, a default.

    Default is taken from Django's LANGUAGE_CODE setting.

    """
    if locale not in LOCALES:
        locale = settings.LANGUAGE_CODE
    return locale


def chunked(iterable, n):
    """Returns chunks of n length of iterable

    If len(iterable) % n != 0, then the last chunk will have length
    less than n.

    Example:

    >>> chunked([1, 2, 3, 4, 5], 2)
    [(1, 2), (3, 4), (5,)]

    """
    iterable = iter(iterable)
    while True:
        t = tuple(islice(iterable, n))
        if t:
            yield t
        else:
            return


def to_class_path(cls):
    """Returns class path for a class

    Takes a class and returns the class path which is composed of the
    module plus the class name. This can be reversed later to get the
    class using ``from_class_path``.

    :returns: string

    >>> from kitsune.search.models import Record
    >>> to_class_path(Record)
    'kitsune.search.models:Record'

    """
    return ':'.join([cls.__module__, cls.__name__])


def from_class_path(cls_path):
    """Returns the class

    Takes a class path and returns the class for it.

    :returns: varies

    >>> from_class_path('kitsune.search.models:Record')
    <Record ...>

    """
    module_path, cls_name = cls_path.split(':')
    module = __import__(module_path, fromlist=[cls_name])
    return getattr(module, cls_name)
