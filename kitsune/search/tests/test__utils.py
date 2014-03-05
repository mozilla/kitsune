from nose.tools import eq_

from kitsune.search.utils import ComposedList, chunked
from kitsune.sumo.tests import TestCase


class TestComposedList(TestCase):
    # See documentation for ComposedList for how it should work.
    def test_no_counts(self):
        cl = ComposedList()

        # No count groups, so length is 0
        eq_(len(cl), 0)

        # Index out of bounds raises an IndexError
        self.assertRaises(IndexError, lambda: cl[0])

        # Slices out of bounds return []
        eq_(cl[0:1], [])

    def test_one(self):
        cl = ComposedList()
        cl.set_count('test', 1)
        eq_(len(cl), 1)
        eq_(cl[0], ('test', 0))
        eq_(cl[0:1], [('test', (0, 1))])

        # Slices out of bounds should return []
        eq_(cl[5:6], [])

    def test_two(self):
        cl = ComposedList()
        cl.set_count('test1', 5)
        cl.set_count('test2', 5)
        eq_(len(cl), 10)
        eq_(cl[0], ('test1', 0))
        eq_(cl[2], ('test1', 2))

        # 5th index in list is 0th index in test2
        eq_(cl[5], ('test2', 0))

        # 6th index in list is 1st index in test2
        eq_(cl[6], ('test2', 1))

        # Test slicing where start and stop are in the same group
        eq_(cl[0:3], [('test1', (0, 3))])
        eq_(cl[7:9], [('test2', (2, 4))])

        # Test slicing where start and stop span groups
        eq_(cl[3:9], [('test1', (3, 5)), ('test2', (0, 4))])

        # Slices out of bounds return []
        eq_(cl[20:25], [])

    def test_three(self):
        cl = ComposedList()
        cl.set_count('test1', 5)
        cl.set_count('test2', 1)
        cl.set_count('test3', 2)

        eq_(len(cl), 8)
        # Slice across everything
        eq_(cl[0:8], [('test1', (0, 5)),
                      ('test2', (0, 1)),
                      ('test3', (0, 2))])

        # Slices out of bounds should return everything
        eq_(cl[0:10], [('test1', (0, 5)),
                       ('test2', (0, 1)),
                       ('test3', (0, 2))])

        # Slice across all three groups
        eq_(cl[4:7], [('test1', (4, 5)),
                      ('test2', (0, 1)),
                      ('test3', (0, 1))])


class ChunkedTests(TestCase):
    def test_chunked(self):
        # chunking nothing yields nothing.
        eq_(list(chunked([], 1)), [])

        # chunking list where len(list) < n
        eq_(list(chunked([1], 10)), [(1,)])

        # chunking a list where len(list) == n
        eq_(list(chunked([1, 2], 2)), [(1, 2)])

        # chunking list where len(list) > n
        eq_(list(chunked([1, 2, 3, 4, 5], 2)),
            [(1, 2), (3, 4), (5,)])

        # passing in a length overrides the real len(list)
        eq_(list(chunked([1, 2, 3, 4, 5, 6, 7], 2, length=4)),
            [(1, 2), (3, 4)])
