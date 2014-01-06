import subprocess
import time
from itertools import islice

from django.conf import settings

import bleach

from kitsune.lib.sumo_locales import LOCALES


call = lambda x: subprocess.Popen(x, stdout=subprocess.PIPE).communicate()


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


def create_batch_id():
    """Returns a batch_id"""
    # TODO: This is silly, but it's a good enough way to distinguish
    # between batches by looking at a Record. This is just over the
    # number of seconds in a day.
    return str(int(time.time()))[-6:]


def chunked(iterable, n):
    """Returns chunks of n length of iterable

    If len(iterable) % n != 0, then the last chunk will have length
    less than n.

    Example:

    >>> chunked([1, 2, 3, 4, 5], 2)
    [(1, 2), (3, 4), (5,)]

    """
    iterable = iter(iterable)
    while 1:
        t = tuple(islice(iterable, n))
        if t:
            yield t
        else:
            return


class ComposedList(object):
    """Takes counts and pretends they're sublists of a big list

    This helps in the case where you know the lengths of the sublists,
    need to treat them all as a big list, but don't want to actually
    have to generate the lists.

    With ComposedList, you do pagination and other things
    including slice the list and get the bounds of the sublists you
    need allowing you to generate just those tiny bits rather than the
    whole thing.

    Handles "length", "index", and "slicing" as if they were
    operations on the complete list.


    **length**

        Length of the ComposedList is the sum of the counts of the
        sublists.

    **index**

        Returns a tuple (kind, index) for the index if the FDL
        were one big list of (kind, index) tuples.

        Raises IndexError if the index exceeds the list.

    **slice**

        Returns a list of (kind, (start, stop)) tuples for the kinds
        that are in the slice bounds. The start and stop are not
        indexes--they're slice start and stop, so it's start up to but
        not including stop.

        For example::

        >>> cl = ComposedList()
        >>> # group a has 5 items indexed 0 through 4
        ...
        >>> cl.set_count('a', 5)
        >>> # group b has 2 items indexed 0 and 1
        ...
        >>> cl.set_count('b', 2)
        >>> cl[1:7]
        [('a', (1, 5)) ('b', (0, 2))]

        This is the same if this were a real list:

        >>> reallist = [('a', 0), ('a', 1), ('a', 2), ('a', 3)
        ...     ('a', 4), ('b', 0), ('b', 1)]
        >>> reallist[1:7]
        [('a', 1), ('a', 2), ('a', 3), ('a', 4), ('b', 0), ('b', 1)]

    """
    def __init__(self):
        self.counts = []

    def set_count(self, kind, count):
        """Adds a (kind, count) to the counts

        >>> cl = ComposedList()
        >>> cl.set_count('wiki', 10)

        :arg kind: str. e.g. 'wiki'
        :arg count: int. e.g. 40

        .. Note::

           The order you call set_count() is important. If you have
           three groups of things, you need to call set_count() in the
           order you want those things returned in a slice.

        """
        self.counts.append((kind, count))

    def __repr__(self):
        return repr(self.counts)

    def __len__(self):
        """Returns the total length of the composed list"""
        return sum(mem[1] for mem in self.counts)

    def __getitem__(self, key):
        """Returns the 'index' or 'slice' of this composed list"""
        if isinstance(key, slice):
            start = key.start
            stop = key.stop
            docs = []

            # figure out the start
            for mem in self.counts:
                if start is not None:
                    if start <= mem[1]:
                        if stop <= mem[1]:
                            docs.append((mem[0], (start, stop)))
                            break
                        docs.append((mem[0], (start, mem[1])))
                        start = None
                    else:
                        start = start - mem[1]
                    stop = stop - mem[1]
                else:
                    if stop <= mem[1]:
                        docs.append((mem[0], (0, stop)))
                        break
                    else:
                        docs.append((mem[0], (0, mem[1])))
                        stop = stop - mem[1]

            return docs

        if isinstance(key, int):
            for mem in self.counts:
                if key < mem[1]:
                    return (mem[0], key)
                else:
                    key = key - mem[1]
            if key >= 0:
                raise IndexError('Index exceeded list length.')
