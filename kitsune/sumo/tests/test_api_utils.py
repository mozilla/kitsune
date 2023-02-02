from datetime import datetime
from unittest.mock import Mock
from zoneinfo import ZoneInfo

from django.test.client import RequestFactory
from django.test.utils import override_settings
from rest_framework import fields, serializers

from kitsune.sumo import api_utils
from kitsune.sumo.tests import TestCase


@override_settings(
    WIKI_DEFAULT_LANGUAGE="en-US",
    SUMO_LANGUAGES=["en-US", "es"],
    NON_SUPPORTED_LOCALES={"es-es": "es", "de": None},
)
class TestLanguageNegotiation(TestCase):
    def test_it_works(self):
        """Make sure that the LocaleNegotiationMixin detects locales."""
        factory = RequestFactory()
        negotiater = api_utils.LocaleNegotiationMixin()
        request = factory.get("/", HTTP_ACCEPT_LANGUAGE="es,en-US")
        negotiater.request = request
        self.assertEqual(negotiater.get_locale(), "es")


class TestInequalityFilterBackend(TestCase):
    def setUp(self):
        self.request = Mock()
        self.view = Mock()
        self.backend = api_utils.InequalityFilterBackend()
        self.queryset = Mock()

        self.queryset.filter.return_value = self.queryset

    def test_gt_whitelist(self):
        """gt works, and that non-whitelisted variables don't get filtered."""
        self.view.filterset_fields = ["x"]
        # `x` should be filtered, but `y` should not, since it is not in
        # `filterset_fields`
        self.request.query_params = {"x__gt": 10, "y": 5}
        self.backend.filter_queryset(self.request, self.queryset, self.view)
        self.queryset.filter.assert_called_with(x__gt=10)

    def test_lt_gte_multiple(self):
        """multiple fields, gte, and lt."""
        self.view.filterset_fields = ["x", "y"]
        self.request.query_params = {"x__gte": 10, "y__lt": 5}
        self.backend.filter_queryset(self.request, self.queryset, self.view)
        calls = self.queryset.method_calls
        # Since both variables are in `filterset_fields`, they both get processed.
        expected = [("filter", (), {"x__gte": 10}), ("filter", (), {"y__lt": 5})]
        self.assertEqual(calls, expected)


class TestDateTimeUTCField(TestCase):
    def test_translation_of_nonnaive(self):
        field = api_utils.DateTimeUTCField()
        as_pacific = datetime(2014, 11, 12, 13, 49, 59, tzinfo=ZoneInfo("US/Pacific"))
        as_utc = field.to_representation(as_pacific)
        self.assertEqual(as_utc, "2014-11-12T21:49:59Z")

    # TODO: How can naive datetime conversion be tested?


class TestPermissionMod(TestCase):
    def test_follows_permissions(self):
        allow = True
        allow_obj = True

        class MockPermission(object):
            def has_permission(self, *args):
                return allow

            def has_object_permission(self, *args):
                return allow_obj

        class MockSerializer(serializers.Serializer):
            foo = api_utils.PermissionMod(fields.ReadOnlyField, [MockPermission])()

        obj = Mock()
        obj.foo = "bar"

        # If either has_permission or has_object_permission returns False,
        # then the field should act as a write_only field. Otherwise it should
        # act as a read/write field .
        cases = [
            # allow, allow_obj, expected_val, expected_write_only
            (True, True, "bar", False),
            (True, False, None, True),
            (False, True, None, True),
            (False, False, None, True),
        ]

        for case in cases:
            allow, allow_obj, expected_val, expected_write_only = case
            serializer = MockSerializer(instance=obj)
            self.assertEqual(serializer.data.get("foo"), expected_val)


class TestJsonRenderer(TestCase):
    def test_it_works(self):
        expected = b'{"foo":"bar"}'
        actual = api_utils.JSONRenderer().render({"foo": "bar"})
        self.assertEqual(expected, actual)

    def test_it_escapes_bracket_slash(self):
        expected = rb'{"xss":"<\/script>"}'
        actual = api_utils.JSONRenderer().render({"xss": "</script>"})
        self.assertEqual(expected, actual)
