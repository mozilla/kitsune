from kitsune.sumo.tests import TestCase
from kitsune.users.tests import UserFactory


class TestLocaleMiddleware(TestCase):
    def test_default_redirect(self):
        # User wants en-us, we send en-US
        response = self.client.get("/search", follow=True, HTTP_ACCEPT_LANGUAGE="en-us")
        self.assertRedirects(response, "/en-US/search/", status_code=302)

        # User wants fr-FR, we send fr
        response = self.client.get("/search", follow=True, HTTP_ACCEPT_LANGUAGE="fr-fr")
        self.assertRedirects(response, "/fr/search/", status_code=302)

        # User wants xy (which doesn't exist), we send en-US
        response = self.client.get("/search", follow=True, HTTP_ACCEPT_LANGUAGE="xy")
        self.assertRedirects(response, "/en-US/search/", status_code=302)

        # User doesn't know what they want, we send en-US
        response = self.client.get("/search", follow=True, HTTP_ACCEPT_LANGUAGE="")
        self.assertRedirects(response, "/en-US/search/", status_code=302)

    def test_mixed_case_header(self):
        """Accept-Language is case insensitive."""
        response = self.client.get("/search", follow=True, HTTP_ACCEPT_LANGUAGE="en-US")
        self.assertRedirects(response, "/en-US/search/", status_code=302)

    def test_specificity(self):
        """Requests for /fr-FR/search should end up on /fr/search"""
        reponse = self.client.get("/fr-FR/search", follow=True)
        self.assertRedirects(reponse, "/fr/search/", status_code=302)

    def test_partial_redirect(self):
        """Ensure that /en/ gets directed to /en-US/."""
        response = self.client.get("/en/search", follow=True)
        self.assertRedirects(response, "/en-US/search/", status_code=302)

    def test_lower_to_upper(self):
        """/en-us should redirect to /en-US."""
        response = self.client.get("/en-us/search", follow=True)
        self.assertRedirects(response, "/en-US/search/", status_code=302)

    def test_upper_accept_lang(self):
        """'en-US' and 'en-us' are both OK in Accept-Language."""
        response = self.client.get("/search", follow=True, HTTP_ACCEPT_LANGUAGE="en-US,fr;q=0.3")
        self.assertRedirects(response, "/en-US/search/", status_code=302)


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
        response = self.client.get("/", follow=True, HTTP_ACCEPT_LANGUAGE="es")
        self.assertRedirects(response, "/es/")

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
        response = self.client.get("/", follow=True, HTTP_ACCEPT_LANGUAGE="es")
        self.assertRedirects(response, "/es/")

    def test_lang_redirects(self):
        response = self.client.get("/questions/?lang=De&utm_source=mdn", follow=True)
        self.assertRedirects(response, "/de/questions/?utm_source=mdn")

        response = self.client.get("/questions/?lang=pt-br&utm_source=mdn", follow=True)
        self.assertRedirects(response, "/pt-BR/questions/?utm_source=mdn")

        response = self.client.get("/questions/?lang=su&utm_source=mdn", follow=True)
        self.assertRedirects(response, "/en-US/questions/?utm_source=mdn")

        response = self.client.get("/questions/?lang=sc&utm_source=mdn", follow=True)
        self.assertRedirects(response, "/it/questions/?utm_source=mdn")


class NonSupportedTests(TestCase):
    def test_middleware(self):
        response = self.client.get("/nn-NO/", follow=True)
        self.assertRedirects(response, "/no/", status_code=302)

        response = self.client.get("/nn-no/", follow=True)
        self.assertRedirects(response, "/no/", status_code=302)

        response = self.client.get("/SU/", follow=True)
        self.assertRedirects(response, "/en-US/", status_code=302)
