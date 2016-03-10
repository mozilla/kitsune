from datetime import datetime

from nose.tools import eq_

from kitsune.customercare.templatetags.jinja_helpers import isotime, round_percent, utctimesince
from kitsune.sumo.tests import TestCase


def test_isotime():
    """Test isotime helper."""
    time = datetime(2009, 12, 25, 10, 11, 12)
    eq_(isotime(time), '2009-12-25T18:11:12Z')

    assert isotime(None) is None


class RoundPercentTests(TestCase):
    """Tests for round_percent."""
    def test_high_percent_int(self):
        eq_('90', str(round_percent(90)))

    def test_high_percent_float(self):
        eq_('90', str(round_percent(90.3456)))

    def test_low_percent_int(self):
        eq_('6.0', str(round_percent(6)))

    def test_low_percent_float(self):
        eq_('6.3', str(round_percent(6.299)))


class UTCTimesinceTests(TestCase):
    """Tests for the utctimesince function

    These are largely copied from sumo.tests.test_helpers.TimesinceTests

    """

    def test_none(self):
        """If None is passed in, utctimesince returns ''."""
        eq_('', utctimesince(None))

    def test_trunc(self):
        """Assert it returns only the most significant time division."""
        eq_('1 year ago',
            utctimesince(datetime(2000, 1, 2), now=datetime(2001, 2, 3)))

    def test_future(self):
        """Test future date and omitting "now" kwarg"""
        eq_('', utctimesince(datetime(9999, 1, 2)))
