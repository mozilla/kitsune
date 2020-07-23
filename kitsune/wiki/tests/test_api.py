from nose.tools import eq_

from kitsune.sumo.urlresolvers import reverse
from kitsune.sumo.tests import TestCase


class TestDocumentListView(TestCase):
    def test_it_works(self):
        url = reverse("document-list")
        res = self.client.get(url)
        eq_(res.status_code, 200)
