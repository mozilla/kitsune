from nose.tools import eq_

from dashboards.readouts import CONTRIBUTOR_READOUTS
from sumo.tests import TestCase, MobileTestCase
from sumo.urlresolvers import reverse


class LocalizationDashTests(TestCase):
    def test_redirect_to_contributor_dash(self):
        """Should redirect to Contributor Dash if the locale is the default"""
        response = self.client.get(reverse('dashboards.localization',
                                           locale='en-US'),
                                   follow=True)
        self.assertRedirects(response, reverse('dashboards.contributors',
                                               locale='en-US'))


class ContributorDashTests(TestCase):
    def test_main_view(self):
        """Assert the top page of the contributor dash resolves, renders."""
        response = self.client.get(reverse('dashboards.contributors',
                                           locale='en-US'))
        eq_(200, response.status_code)

    def test_detail_view(self):
        """Assert the detail page of the contributor dash resolves, renders."""
        response = self.client.get(reverse('dashboards.contributors_detail',
            args=[CONTRIBUTOR_READOUTS[CONTRIBUTOR_READOUTS.keys()[0]].slug],
            locale='en-US'))
        eq_(200, response.status_code)


class MobileHomeTests(MobileTestCase):
    def test_desktop_home_for_mobile(self):
        r = self.client.get(reverse('home'), follow=True)
        eq_(r.status_code, 200)
        self.assertTemplateUsed(r, 'dashboards/mobile/home.html')

    def test_mobile_home_for_mobile(self):
        r = self.client.get(reverse('home.mobile'), follow=True)
        eq_(r.status_code, 200)
        self.assertTemplateUsed(r, 'dashboards/mobile/mobile.html')
