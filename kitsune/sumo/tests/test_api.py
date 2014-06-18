from django.test.client import RequestFactory
from django.test.utils import override_settings
from nose.tools import eq_

from kitsune.sumo.api import LocaleNegotiationMixin
from kitsune.sumo.tests import TestCase


@override_settings(WIKI_DEFAULT_LANGUAGE='en-US',
                   SUMO_LANGUAGES=['en-US', 'es'],
                   NON_SUPPORTED_LOCALES={'es-es': 'es', 'de': None})
class TestLanguageNegotiation(TestCase):

    def test_it_works(self):
        #, accept_language, expected):
        """Make sure that the LocaleNegotiationMixin detects locales."""
        factory = RequestFactory()
        negotiater = LocaleNegotiationMixin()
        request = factory.get('/', HTTP_ACCEPT_LANGUAGE='es,en-US')
        negotiater.request = request
        eq_(negotiater.get_locale(), 'es')
