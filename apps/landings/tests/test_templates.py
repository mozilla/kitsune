from sumo.tests import TestCase
from sumo.urlresolvers import reverse


class MobileHomeTestCase(TestCase):
    def test_top_text(self):
        response = self.client.get(reverse('home.mobile'), follow=True)
        self.assertContains(response, 'Firefox Help for Mobile')

    def test_no_plugin_check(self):
        response = self.client.get(reverse('home.mobile'), follow=True)
        self.assertNotContains(response, 'run an instant check')
