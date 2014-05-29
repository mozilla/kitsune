from django.test.client import RequestFactory
from django.test.utils import override_settings
from nose.tools import eq_

from kitsune.sumo.api import LocaleNegotiationMixin
from kitsune.sumo.tests import TestCase


@override_settings(WIKI_DEFAULT_LANGUAGE='en-US',
                   SUMO_LANGUAGES=['en-US', 'es'],
                   NON_SUPPORTED_LOCALES={'es-es': 'es', 'de': None})
class TestLanguageNegotiation(TestCase):

    def _run(self, accept_language, expected):
        """Negotiate a Accept-Language and compare it to the expected value."""
        factory = RequestFactory()
        negotiater = LocaleNegotiationMixin()
        request = factory.get('/', HTTP_ACCEPT_LANGUAGE=accept_language)
        negotiater.request = request
        eq_(negotiater.get_locale(), expected)

    def test_basic(self):
        """Test that simple accept headers work."""
        self._run('en-US', 'en-US')

    def test_selection(self):
        """Test that it will select a non-default language."""
        self._run('es,en-US', 'es')

    def test_fallback(self):
        """Test that NON_SUPPORTED_LOCALES fallback correctly."""
        self._run('es-es,en-US', 'es')
        self._run('de,es', 'es')
        self._run('es-es,de,en-US', 'es')

    def test_order(self):
        """Test that order matters."""
        self._run('es,en-US', 'es')
        self._run('en-US,es', 'en-US')

    def test_unknown_skip(self):
        """Unknown languages should be skipped."""
        self._run('as,df,es', 'es')

    def test_default(self):
        """Check that if no locale is matched, it returns the default."""
        self._run('as,df', 'en-US')

    def test_extras(self):
        """Somtimes the header has extra stuff. It should be ignored."""
        self._run('es;q=0.5,en-US', 'es')
        self._run('de;q=0.6,es;q=0.4', 'es')

    def test_real_stuff(self):
        """These are actual Accept-Language headers from real users."""
        self._run('en-US,en;q=0.5', 'en-US')
        self._run('en-us,en;q=0.8,es;q=0.5,es-es;q=0.3', 'en-US')
