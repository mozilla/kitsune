from django.test import SimpleTestCase

from kitsune.retrieval.validation import (
    is_finite_number,
    is_int,
    is_nonnegative_int,
    is_positive_int,
)


class ValidationPredicateTests(SimpleTestCase):
    def test_is_int(self):
        for value in (0, -3, 7):
            self.assertTrue(is_int(value), value)
        for value in (True, False, 1.0, "1", None, float("nan")):
            self.assertFalse(is_int(value), value)

    def test_is_positive_int(self):
        self.assertTrue(is_positive_int(1))
        for value in (0, -1, True, 1.0, "1", None):
            self.assertFalse(is_positive_int(value), value)

    def test_is_nonnegative_int(self):
        for value in (0, 5):
            self.assertTrue(is_nonnegative_int(value), value)
        for value in (-1, True, 0.0, "0", None):
            self.assertFalse(is_nonnegative_int(value), value)

    def test_is_finite_number(self):
        for value in (0, -2, 3.5):
            self.assertTrue(is_finite_number(value), value)
        for value in (True, False, float("nan"), float("inf"), float("-inf"), "1", None):
            self.assertFalse(is_finite_number(value), value)
