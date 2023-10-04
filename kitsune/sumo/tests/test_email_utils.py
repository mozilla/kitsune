from unittest.mock import patch

from django.conf import settings
from django.contrib.sites.models import Site
from django.utils.functional import lazy
from django.utils import translation
from django.utils.translation import get_language

from kitsune.sumo.email_utils import emails_with_users_and_watches, safe_translation
from kitsune.sumo.tests import TestCase
from kitsune.users.tests import UserFactory

mock_translations = {
    "Hello": {"en-us": "Hello", "fr": "Bonjour", "es": "Hola"},
    "Hello {name}": {
        "en-us": "Hello {name}",
        "fr": "Bonjour {0}",
        "es": "Hola {name}",
    },
}


def mock_ugettext(msg_id):
    locale = get_language()
    return mock_translations[msg_id][locale]


mock_gettext_lazy = lazy(mock_ugettext)


def mock_gettext(f):
    f = patch("django.utils.translation.gettext", mock_ugettext)(f)
    f = patch("django.utils.translation.gettext_lazy", mock_gettext_lazy)(f)
    return f


class SafeTranslationTests(TestCase):
    def setUp(self):
        # These tests assume English is the fall back language. If it
        # isn't we are gonna have a bad time.
        self.assertEqual("en-US", settings.WIKI_DEFAULT_LANGUAGE)

    @mock_gettext
    def test_mocked_gettext(self):
        """I'm not entirely sure about the mocking, so test that."""
        # Import translation now so it is affected by the mock.
        from django.utils.translation import gettext as _

        with translation.override("en-US"):
            self.assertEqual(_("Hello"), "Hello")
        with translation.override("fr"):
            self.assertEqual(_("Hello"), "Bonjour")
        with translation.override("es"):
            self.assertEqual(_("Hello"), "Hola")

    @mock_gettext
    def test_safe_translation_noop(self):
        """Test that safe_translation doesn't mess with good translations."""
        # Import translation now so it is affected by the mock.
        from django.utils.translation import gettext as _

        @safe_translation
        def simple(locale):
            return _("Hello")

        # These should just work normally.
        self.assertEqual(simple("en-US"), "Hello")
        self.assertEqual(simple("fr"), "Bonjour")
        self.assertEqual(simple("es"), "Hola")

    @mock_gettext
    def test_safe_translation_bad_trans(self):
        """Test that safe_translation insulates from bad translations."""
        # Import translation now so it is affected by the mock.
        from django.utils.translation import gettext as _

        # `safe_translation` will call this with the given locale, and
        # if that fails, fall back to English.
        @safe_translation
        def bad_trans(locale):
            return _("Hello {name}").format(name="Mike")

        # French should come back as English, because it has a bad
        # translation, but Spanish should come back in Spanish.
        self.assertEqual(bad_trans("en-US"), "Hello Mike")
        self.assertEqual(bad_trans("fr"), "Hello Mike")
        self.assertEqual(bad_trans("es"), "Hola Mike")

    @mock_gettext
    @patch("kitsune.sumo.email_utils.log")
    def test_safe_translation_logging(self, mocked_log):
        """Logging translation errors is really important, so test it."""
        # Import translation now so it is affected by the mock.
        from django.utils.translation import gettext as _

        # Assert that bad translations cause error logging.
        @safe_translation
        def bad_trans(locale):
            return _("Hello {name}").format(name="Mike")

        # English and Spanish should not log anything. French should.
        bad_trans("en-US")
        bad_trans("es")
        self.assertEqual(len(mocked_log.method_calls), 0)
        bad_trans("fr")
        self.assertEqual(len(mocked_log.method_calls), 1)

        method_name, method_args, method_kwargs = mocked_log.method_calls[0]
        self.assertEqual(method_name, "exception")
        assert "Bad translation" in method_args[0]
        self.assertEqual(method_args[1], "fr")


class PremailerTests(TestCase):
    def test_styles_inlining(self):
        """Test that styles tags are converted to inline styles"""
        with patch("kitsune.sumo.email_utils.render_to_string") as mocked:
            mocked.return_value = (
                "<html>"
                "<head>"
                "<style>a { color: #000; }</style>"
                "</head>"
                "<body>"
                '<a href="/test">Hyperlink</a>'
                "</body>"
                "</html>"
            )

            u = UserFactory()
            msg = emails_with_users_and_watches("test", "a.ltxt", "a.html", {}, [(u, [None])])

            for m in msg:
                tag = '<a href="https://%s/test" style="color:#000">Hyperlink</a>'
                self.assertIn(tag % Site.objects.get_current().domain, str(m.message()))
