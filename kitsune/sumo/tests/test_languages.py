from django.test import SimpleTestCase, modify_settings, override_settings
from django.utils.translation import activate, deactivate, gettext
from django.apps.config import AppConfig


@modify_settings(INSTALLED_APPS={"append": "kitsune.sumo.tests"})
@override_settings(FALLBACK_LANGUAGES={"xx": "yy"})
class FallbackLanguageTests(SimpleTestCase):
    def setUp(self):
        super().setUp()
        # re-run ready as we've changed the settings
        AppConfig.create("kitsune.sumo").ready()
        activate("xx")

    def tearDown(self):
        deactivate()
        super().tearDown()

    def test_no_fallback(self):
        self.assertEqual(gettext("Test 1 (en)"), "Test 1 (xx)")

    def test_fallback_to_yy(self):
        self.assertEqual(gettext("Test 2 (en)"), "Test 2 (yy)")

    def test_fallback_to_msgid(self):
        self.assertEqual(gettext("Test 3 (msgid)"), "Test 3 (msgid)")
