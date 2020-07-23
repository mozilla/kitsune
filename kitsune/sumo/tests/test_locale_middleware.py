from django.conf import settings
from django.test import override_settings

from nose.tools import eq_

from kitsune.sumo.tests import TestCase
from kitsune.sumo.urlresolvers import get_best_language, get_non_supported
from kitsune.users.tests import UserFactory


class TestLocaleMiddleware(TestCase):
    def test_default_redirect(self):
        # User wants en-us, we send en-US
        response = self.client.get("/search", follow=True, HTTP_ACCEPT_LANGUAGE="en-us")
        self.assertRedirects(response, "/en-US/search", status_code=302)

        # User wants fr-FR, we send fr
        response = self.client.get("/search", follow=True, HTTP_ACCEPT_LANGUAGE="fr-fr")
        self.assertRedirects(response, "/fr/search", status_code=302)

        # User wants xy (which doesn't exist), we send en-US
        response = self.client.get("/search", follow=True, HTTP_ACCEPT_LANGUAGE="xy")
        self.assertRedirects(response, "/en-US/search", status_code=302)

        # User doesn't know what they want, we send en-US
        response = self.client.get("/search", follow=True, HTTP_ACCEPT_LANGUAGE="")
        self.assertRedirects(response, "/en-US/search", status_code=302)

    def test_mixed_case_header(self):
        """Accept-Language is case insensitive."""
        response = self.client.get("/search", follow=True, HTTP_ACCEPT_LANGUAGE="en-US")
        self.assertRedirects(response, "/en-US/search", status_code=302)

    def test_specificity(self):
        """Requests for /fr-FR/search should end up on /fr/search"""
        reponse = self.client.get("/fr-FR/search", follow=True)
        self.assertRedirects(reponse, "/fr/search", status_code=302)

    def test_partial_redirect(self):
        """Ensure that /en/ gets directed t /en-US/."""
        response = self.client.get("/en/search", follow=True)
        self.assertRedirects(response, "/en-US/search", status_code=302)

    def test_lower_to_upper(self):
        """/en-us should redirect to /en-US."""
        response = self.client.get("/en-us/search", follow=True)
        self.assertRedirects(response, "/en-US/search", status_code=302)

    def test_upper_accept_lang(self):
        """'en-US' and 'en-us' are both OK in Accept-Language."""
        response = self.client.get("/search", follow=True, HTTP_ACCEPT_LANGUAGE="en-US,fr;q=0.3")
        self.assertRedirects(response, "/en-US/search", status_code=302)


class BestLanguageTests(TestCase):
    def test_english_only(self):
        best = get_best_language("en-us, en;q=0.8")
        eq_("en-US", best)

    def test_en_GB(self):
        """Stick with English if you can."""
        best = get_best_language("en-gb, fr;q=0.8")
        eq_("en-US", best)

    def test_not_worst_choice(self):
        """Try not to fall back to 'es' here."""
        best = get_best_language("en-gb, en;q=0.8, fr-fr;q=0.6, es;q=0.2")
        eq_("en-US", best)

    def test_fr_FR(self):
        best = get_best_language("fr-FR, es;q=0.8")
        eq_("fr", best)

    def test_non_existent(self):
        best = get_best_language("xy-YY, xy;q=0.8")
        eq_(False, best)

    def test_prefix_matching(self):
        """en-US is a better match for en-gb, es;q=0.2 than es."""
        best = get_best_language("en-gb, es;q=0.2")
        eq_("en-US", best)


class PreferredLanguageTests(TestCase):
    def test_anonymous_change_language(self):
        # should set the cookie for the correct language.
        self.client.get("/?lang=zh-CN", follow=True)
        response = self.client.get("/", follow=True)
        self.assertRedirects(response, "/zh-CN/")

        self.client.get("/?lang=en-US", follow=True)
        response = self.client.get("/", follow=True)
        self.assertRedirects(response, "/en-US/")

    def test_loggedin_preferred_language(self):
        u = UserFactory(profile__locale="zh-CN")
        self.client.login(username=u.username, password="testpass")
        response = self.client.get("/", follow=True)
        self.assertRedirects(response, "/zh-CN/")

        self.client.logout()
        response = self.client.get("/", follow=True, HTTP_ACCEPT_LANGUAGE="xx")
        self.assertRedirects(response, "/xx/")

    def test_anonymous_change_to_login(self):
        u = UserFactory(profile__locale="zh-CN")

        # anonymous is fr
        self.client.get("/?lang=fr", follow=True)
        response = self.client.get("/", follow=True)
        self.assertRedirects(response, "/fr/")

        # logged in is zh-CN
        self.client.login(username=u.username, password="testpass")
        response = self.client.get("/", follow=True)
        self.assertRedirects(response, "/zh-CN/")

        # anonymous again, session is now destroyed
        self.client.logout()
        response = self.client.get("/", follow=True, HTTP_ACCEPT_LANGUAGE="xx")
        self.assertRedirects(response, "/xx/")


class NonSupportedTests(TestCase):
    @override_settings(NON_SUPPORTED_LOCALES={"nn-NO": "no", "xx": None})
    def test_get_non_supported(self):
        eq_("no", get_non_supported("nn-NO"))
        eq_("no", get_non_supported("nn-no"))
        eq_(settings.LANGUAGE_CODE, get_non_supported("xx"))
        eq_(None, get_non_supported("yy"))

    @override_settings(NON_SUPPORTED_LOCALES={"nn-NO": "no", "xy": None})
    def test_middleware(self):
        response = self.client.get("/nn-NO/", follow=True)
        self.assertRedirects(response, "/no/", status_code=302)

        response = self.client.get("/nn-no/", follow=True)
        self.assertRedirects(response, "/no/", status_code=302)

        response = self.client.get("/xy/", follow=True)
        self.assertRedirects(response, "/en-US/", status_code=302)
