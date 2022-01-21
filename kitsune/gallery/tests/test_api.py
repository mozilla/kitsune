from kitsune.sumo.tests import TestCase
from kitsune.sumo.urlresolvers import reverse


class TestImageListView(TestCase):
    def test_it_works(self):
        url = reverse("image-list")
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)
