from nose.tools import eq_

from sumo.tests import TestCase
from sumo.urlresolvers import get_best_language


class TestLocaleMiddleware(TestCase):
    def test_default_redirect(self):
        # User wants en-us, we send en-US
        response = self.client.get('/search', follow=True,
                                   HTTP_ACCEPT_LANGUAGE='en-us')
        self.assertRedirects(response, '/en-US/search', status_code=302)

        # User wants fr-FR, we send fr
        response = self.client.get('/search', follow=True,
                                   HTTP_ACCEPT_LANGUAGE='fr-fr')
        self.assertRedirects(response, '/fr/search', status_code=302)

        # User wants xx, we send en-US
        response = self.client.get('/search', follow=True,
                                   HTTP_ACCEPT_LANGUAGE='xx')
        self.assertRedirects(response, '/en-US/search', status_code=302)

        # User doesn't know what they want, we send en-US
        response = self.client.get('/search', follow=True,
                                   HTTP_ACCEPT_LANGUAGE='')
        self.assertRedirects(response, '/en-US/search', status_code=302)

    def test_mixed_case_header(self):
        """Accept-Language is case insensitive."""
        response = self.client.get('/search', follow=True,
                                   HTTP_ACCEPT_LANGUAGE='en-US')
        self.assertRedirects(response, '/en-US/search', status_code=302)

    def test_specificity(self):
        """Requests for /fr-FR/search should end up on /fr/search"""
        reponse = self.client.get('/fr-FR/search', follow=True)
        self.assertRedirects(reponse, '/fr/search', status_code=302)

    def test_partial_redirect(self):
        """Ensure that /en/ gets directed to /en-US/."""
        response = self.client.get('/en/search', follow=True)
        self.assertRedirects(response, '/en-US/search', status_code=302)

    def test_lower_to_upper(self):
        """/en-us should redirect to /en-US."""
        response = self.client.get('/en-us/search', follow=True)
        self.assertRedirects(response, '/en-US/search', status_code=302)

    def test_upper_accept_lang(self):
        """'en-US' and 'en-us' are both OK in Accept-Language."""
        response = self.client.get('/search', follow=True,
                                   HTTP_ACCEPT_LANGUAGE='en-US,fr;q=0.3')
        self.assertRedirects(response, '/en-US/search', status_code=302)


class BestLanguageTests(TestCase):
    def test_english_only(self):
        best = get_best_language('en-us, en;q=0.8')
        eq_('en-US', best)

    def test_en_GB(self):
        """Stick with English if you can."""
        best = get_best_language('en-gb, fr;q=0.8')
        eq_('en-US', best)

    def test_not_worst_choice(self):
        """Try not to fall back to 'es' here."""
        best = get_best_language('en-gb, en;q=0.8, fr-fr;q=0.6, es;q=0.2')
        eq_('en-US', best)

    def test_fr_FR(self):
        best = get_best_language('fr-FR, es;q=0.8')
        eq_('fr', best)

    def test_non_existent(self):
        best = get_best_language('xx-YY, xx;q=0.8')
        eq_(False, best)

    def test_prefix_matching(self):
        """en-US is a better match for en-gb, es;q=0.2 than es."""
        best = get_best_language('en-gb, es;q=0.2')
        eq_('en-US', best)
