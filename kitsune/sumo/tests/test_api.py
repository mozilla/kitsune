from mock import Mock
from nose.tools import eq_

from django.test.client import RequestFactory
from django.test.utils import override_settings

from kitsune.sumo.api import LocaleNegotiationMixin, InequalityFilterBackend
from kitsune.sumo.tests import TestCase


@override_settings(WIKI_DEFAULT_LANGUAGE='en-US',
                   SUMO_LANGUAGES=['en-US', 'es'],
                   NON_SUPPORTED_LOCALES={'es-es': 'es', 'de': None})
class TestLanguageNegotiation(TestCase):

    def test_it_works(self):
        """Make sure that the LocaleNegotiationMixin detects locales."""
        factory = RequestFactory()
        negotiater = LocaleNegotiationMixin()
        request = factory.get('/', HTTP_ACCEPT_LANGUAGE='es,en-US')
        negotiater.request = request
        eq_(negotiater.get_locale(), 'es')


class TestInequalityFilterBackend(TestCase):

    def setUp(self):
        self.request = Mock()
        self.view = Mock()
        self.backend = InequalityFilterBackend()
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
