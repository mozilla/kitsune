from nose.tools import eq_

from kitsune.search.v2.tests import Elastic7TestCase
from kitsune.sumo.tests import LocalizingClient
from kitsune.sumo.urlresolvers import reverse


class ContributorsMetricsTests(Elastic7TestCase):
    """Tests for the Community Hub user search page."""

    client_class = LocalizingClient
    search_tests = True

    def test_it_works(self):
        url = reverse("community.metrics")
        res = self.client.get(url)
        eq_(res.status_code, 200)
