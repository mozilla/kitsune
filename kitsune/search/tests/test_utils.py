from nose.tools import eq_

from kitsune.search.utils import chunked, from_class_path, to_class_path
from kitsune.sumo.tests import TestCase


class ChunkedTests(TestCase):
    def test_chunked(self):
        # chunking nothing yields nothing.
        eq_(list(chunked([], 1)), [])

        # chunking list where len(list) < n
        eq_(list(chunked([1], 10)), [(1,)])

        # chunking a list where len(list) == n
        eq_(list(chunked([1, 2], 2)), [(1, 2)])

        # chunking list where len(list) > n
        eq_(list(chunked([1, 2, 3, 4, 5], 2)), [(1, 2), (3, 4), (5,)])


class FooBarClassOfAwesome(object):
    pass


def test_from_class_path():
    eq_(
        from_class_path("kitsune.search.tests.test_utils:FooBarClassOfAwesome"),
        FooBarClassOfAwesome,
    )


def test_to_class_path():
    eq_(
        to_class_path(FooBarClassOfAwesome),
        "kitsune.search.tests.test_utils:FooBarClassOfAwesome",
    )
