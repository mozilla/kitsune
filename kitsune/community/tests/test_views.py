from nose.tools import eq_

from kitsune.sumo.tests import LocalizingClient
from kitsune.sumo.urlresolvers import reverse
from kitsune.search.tests import ElasticTestCase


class ContributorsMetricsTests(ElasticTestCase):
    """Tests for the Community Hub user search page."""

    client_class = LocalizingClient

    def test_it_works(self):
        url = reverse("community.metrics")
        res = self.client.get(url)
        eq_(res.status_code, 200)
