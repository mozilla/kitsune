# -*- coding: utf8 -*-
from mock import patch
from nose.tools import eq_

from django.utils.translation import get_language
from django.utils.functional import lazy

from sumo.email_utils import uselocale, safe_translation
from sumo.tests import TestCase


mock_translations = {
    'Hello': {
        'en-us': 'Hello',
        'fr': 'Bonjour',
        'es': 'Hola',
    },
    'Hello {name}': {
        'en-us': 'Hello {name}',
        'fr': 'Bonjour {0}',
        'es': 'Hola {name}',
    }
}


def mock_ugettext(msg_id):
    locale = get_language()
    return mock_translations[msg_id][locale]

mock_ugettext_lazy = lazy(mock_ugettext)


def mock_gettext(f):
    f = patch('tower.ugettext', mock_ugettext)(f)
    f = patch('tower.ugettext_lazy', mock_ugettext_lazy)(f)
    return f


class SafeTranslationTests(TestCase):

    @mock_gettext
    def test_mocked_gettext(self):
        """I'm not entirely sure about the mocking, so test that."""
        # Import tower now so it is affected by the mock.
        from tower import ugettext as _

        with uselocale('en-US'):
            eq_(_('Hello'), 'Hello')
        with uselocale('fr'):
            eq_(_('Hello'), 'Bonjour')
        with uselocale('es'):
            eq_(_('Hello'), 'Hola')

    @mock_gettext
    def test_safe_translation_noop(self):
        """Test that safe_translation doesn't mess with good translations."""
        # Import tower now so it is affected by the mock.
        from tower import ugettext as _

        @safe_translation
        def simple(locale):
            return _('Hello')

        # These should just work normally.
        eq_(simple('en-US'), 'Hello')
        eq_(simple('fr'), 'Bonjour')
        eq_(simple('es'), 'Hola')

    @mock_gettext
    def test_safe_translation_bad_trans(self):
        """Test that safe_translation insulates from bad translations."""
        # Import tower now so it is affected by the mock.
        from tower import ugettext as _

        # `safe_translation` will call this with the given locale, and
        # if that fails, fall back to English.
        @safe_translation
        def bad_trans(locale):
            return _('Hello {name}').format(name='Mike')

        # French should come back as English, because it has a bad
        # translation, but Spanish should come back in Spanish.
        eq_(bad_trans('en-US'), 'Hello Mike')
        eq_(bad_trans('fr'), 'Hello Mike')
        eq_(bad_trans('es'), 'Hola Mike')


class UseLocaleTests(TestCase):

    def test_uselocale(self):
        """Test that uselocale does what it says on the tin."""
        with uselocale('en-US'):
            eq_(get_language(), 'en-us')
        with uselocale('de'):
            eq_(get_language(), 'de')
        with uselocale('fr'):
            eq_(get_language(), 'fr')
