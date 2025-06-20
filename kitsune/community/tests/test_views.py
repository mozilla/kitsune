from kitsune.search.tests import ElasticTestCase
from kitsune.sumo.urlresolvers import reverse


class ContributorsMetricsTests(ElasticTestCase):
    """Tests for the Community Hub user search page."""

    search_tests = True

    def test_it_works(self):
        url = reverse("community.metrics")
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)
