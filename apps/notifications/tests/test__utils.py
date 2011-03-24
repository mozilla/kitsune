from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from mock import patch
from nose.tools import eq_, raises

from notifications.tests import TestCase
from notifications.utils import collate, import_from_setting


class MergeTests(TestCase):
    """Unit tests for collate()"""
    # Also accidentally tests peekable, though that could use its own tests

    def test_default(self):
        """Test with the default `key` function."""
        iterables = [xrange(4), xrange(7), xrange(3, 6)]
        eq_(sorted(reduce(list.__add__, [list(it) for it in iterables])),
            list(collate(*iterables)))

    def test_key(self):
        """Test using a custom `key` function."""
        iterables = [xrange(5, 0, -1), xrange(4, 0, -1)]
        eq_(list(sorted(reduce(list.__add__,
                                        [list(it) for it in iterables]),
                        reverse=True)),
            list(collate(*iterables, key=lambda x: -x)))

    def test_empty(self):
        """Be nice if passed an empty list of iterables."""
        eq_([], list(collate()))

    def test_one(self):
        """Work when only 1 iterable is passed."""
        eq_([0, 1], list(collate(xrange(2))))

    def test_reverse(self):
        """Test the `reverse` kwarg."""
        iterables = [xrange(4, 0, -1), xrange(7, 0, -1), xrange(3, 6, -1)]
        eq_(sorted(reduce(list.__add__, [list(it) for it in iterables]),
                   reverse=True),
            list(collate(*iterables, reverse=True)))


class ImportedFromSettingTests(TestCase):
    """Tests for import_from_setting() and _imported_symbol()"""

    @patch.object(settings._wrapped,
                  'NOTIFICATIONS_MODEL_BASE',
                  'django.db.models.Model',
                  create=True)
    def test_success(self):
        from django.db.models import Model
        assert import_from_setting('NOTIFICATIONS_MODEL_BASE', 'blah') == Model

    @raises(ImproperlyConfigured)
    @patch.object(settings._wrapped,
                  'NOTIFICATIONS_MODEL_BASE',
                  'hummahummanookanookanonexistent.thing',
                  create=True)
    def test_module_missing(self):
        import_from_setting('NOTIFICATIONS_MODEL_BASE', 'blah')

    @raises(ImproperlyConfigured)
    @patch.object(settings._wrapped,
                  'NOTIFICATIONS_MODEL_BASE',
                  'django.hummahummanookanookanonexistent',
                  create=True)
    def test_symbol_missing(self):
        import_from_setting('NOTIFICATIONS_MODEL_BASE', 'blah')
