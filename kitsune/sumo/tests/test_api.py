import pytz
from datetime import datetime
from mock import Mock
from nose.tools import eq_

from django.test.client import RequestFactory
from django.test.utils import override_settings

from rest_framework import fields

from kitsune.sumo import api
from kitsune.sumo.tests import TestCase


@override_settings(WIKI_DEFAULT_LANGUAGE='en-US',
                   SUMO_LANGUAGES=['en-US', 'es'],
                   NON_SUPPORTED_LOCALES={'es-es': 'es', 'de': None})
class TestLanguageNegotiation(TestCase):

    def test_it_works(self):
        """Make sure that the LocaleNegotiationMixin detects locales."""
        factory = RequestFactory()
        negotiater = api.LocaleNegotiationMixin()
        request = factory.get('/', HTTP_ACCEPT_LANGUAGE='es,en-US')
        negotiater.request = request
        eq_(negotiater.get_locale(), 'es')


class TestInequalityFilterBackend(TestCase):

    def setUp(self):
        self.request = Mock()
        self.view = Mock()
        self.backend = api.InequalityFilterBackend()
        self.queryset = Mock()

        self.queryset.filter.return_value = self.queryset

    def test_gt_whitelist(self):
        """gt works, and that non-whitelisted variables don't get filtered."""
        self.view.filter_fields = ['x']
        # `x` should be filtered, but `y` should not, since it is not in
        # `filter_fields`
        self.request.QUERY_PARAMS = {'x__gt': 10, 'y': 5}
        self.backend.filter_queryset(self.request, self.queryset, self.view)
        self.queryset.filter.assert_called_with(x__gt=10)

    def test_lt_gte_multiple(self):
        """multiple fields, gte, and lt."""
        self.view.filter_fields = ['x', 'y']
        self.request.QUERY_PARAMS = {'x__gte': 10, 'y__lt': 5}
        self.backend.filter_queryset(self.request, self.queryset, self.view)
        calls = sorted(self.queryset.method_calls)
        # Since both variables are in `filter_fields`, they both get processed.
        expected = [('filter', (), {'x__gte': 10}),
                    ('filter', (), {'y__lt': 5})]
        eq_(calls, expected)


class TestDateTimeUTCField(TestCase):

    def test_translation_of_nonnaive(self):
        field = api.DateTimeUTCField()
        as_pacific = datetime(2014, 11, 12, 13, 49, 59, tzinfo=pytz.timezone('US/Pacific'))
        as_utc = field.to_native(as_pacific)
        eq_(as_utc.hour, 21)
        eq_(as_utc.tzinfo, pytz.utc)

    # TODO: How can naive datetime conversion be tested?


class TestPermissionMod(TestCase):

    def test_write_only(self):
        field = api.PermissionMod(fields.WritableField, [])()

        cases = [
            (False, False, False),
            (False, True, True),
            (True, False, True),
            (True, True, True)
        ]

        for case in cases:
            field._write_only, field._stealth, expected = case
            eq_(field.write_only, expected)

    def test_follows_permissions(self):
        allow = True
        allow_obj = True

        class MockPermission(object):
            def has_permission(self, *args):
                return allow

            def has_object_permission(self, *args):
                return allow_obj

        serializer = Mock()
        obj = Mock()
        obj.foo = 'bar'
        field = api.PermissionMod(fields.WritableField, [MockPermission])()
        field.initialize(serializer, 'foo')

        # If either has_permission or has_object_permission returns False,
        # then the field should act as a write_only field. Otherwise it shld
        # act as a read/write field .
        cases = [
            (True, True, 'bar', False),
            (True, False, None, True),
            (False, True, None, True),
            (False, False, None, True),
        ]

        for case in cases:
            allow, allow_obj, expected_val, expected_write = case
            eq_(field.field_to_native(obj, 'foo'), expected_val)
            eq_(field.write_only, expected_write)
