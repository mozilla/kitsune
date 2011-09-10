from nose.tools import eq_

from bleach import clean

from chat.utils import Safe
from sumo.tests import TestCase


class SafeTests(TestCase):
    """Tests for Safe wrapper"""

    def test_clean_strings(self):
        eq_(clean('<br />'), Safe.escape('<br />'))

    def test_dont_clean_nonstrings(self):
        eq_(9, Safe.escape(9))

    def test_dont_clean_safes(self):
        eq_('<br />', Safe.escape(Safe('<br />')))
