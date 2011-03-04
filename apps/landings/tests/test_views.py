from nose.tools import eq_

from sumo.tests import MobileTestCase
from sumo.urlresolvers import reverse


class MobileHomeTests(MobileTestCase):
    def test_desktop_home_for_mobile(self):
        r = self.client.get(reverse('home'), follow=True)
        eq_(r.status_code, 200)
        self.assertTemplateUsed(r, 'landings/mobile/home.html')

    def test_mobile_home_for_mobile(self):
        r = self.client.get(reverse('home.mobile'), follow=True)
        eq_(r.status_code, 200)
        self.assertTemplateUsed(r, 'landings/mobile/mobile.html')
