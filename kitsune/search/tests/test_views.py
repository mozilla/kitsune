import json

from pyquery import PyQuery as pq

from kitsune.search.tests import Elastic7TestCase
from kitsune.sumo.urlresolvers import reverse


class TestSearchSEO(Elastic7TestCase):
    """Test SEO-related aspects of the SUMO search view."""

    def test_simple_search(self):
        """
        Test SEO-related response for search.
        """
        url = reverse("search", locale="en-US")
        response = self.client.get(f"{url}?q=firefox")
        self.assertEqual(response.status_code, 200)
        self.assertTrue("text/html" in response["content-type"])
        doc = pq(response.content)
        self.assertEqual(doc('meta[name="robots"]').attr("content"), "noindex, nofollow")
        # TODO: Are these old Webtrends meta tags even useful any longer?
        self.assertEqual(doc('meta[name="WT.oss"]').attr("content"), "firefox")
        self.assertEqual(doc('meta[name="WT.oss_r"]').attr("content"), "0")

    def test_simple_search_json(self):
        """
        Test SEO-related response for search when JSON is requested.
        """
        url = reverse("search", locale="en-US")
        response = self.client.get(f"{url}?format=json&q=firefox")
        self.assertEqual(response.status_code, 200)
        self.assertTrue("application/json" in response["content-type"])
        self.assertTrue("x-robots-tag" in response)
        self.assertEqual(response["x-robots-tag"], "noindex, nofollow")

    def test_invalid_search(self):
        """
        Test SEO-related response for invalid search.
        """
        url = reverse("search", locale="en-US")
        response = self.client.get(f"{url}?abc=firefox")
        self.assertEqual(response.status_code, 200)
        self.assertTrue("text/html" in response["content-type"])
        doc = pq(response.content)
        self.assertEqual(doc('meta[name="robots"]').attr("content"), "noindex, nofollow")
        # TODO: Are these old Webtrends meta tags even useful any longer?
        self.assertFalse(doc.find('meta[name="WT.oss"]'))
        self.assertFalse(doc.find('meta[name="WT.oss_r"]'))

    def test_invalid_search_json(self):
        """
        Test SEO-related response for invalid search when JSON is requested.
        """
        url = reverse("search", locale="en-US")
        response = self.client.get(f"{url}?format=json&abc=firefox")
        self.assertEqual(response.status_code, 400)
        self.assertTrue("application/json" in response["content-type"])
        self.assertEqual(json.loads(response.content), {"error": "Invalid search data."})
        self.assertTrue("x-robots-tag" in response)
        self.assertEqual(response["x-robots-tag"], "noindex")
