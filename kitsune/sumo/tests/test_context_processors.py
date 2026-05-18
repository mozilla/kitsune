from django.test.client import RequestFactory

from kitsune.sumo.context_processors import geoip
from kitsune.sumo.tests import TestCase


class GeoIPContextProcessorTestCase(TestCase):
    def test_geo_headers_present(self):
        rf = RequestFactory()
        request = rf.get("/")
        request.META["HTTP_X_CLIENT_GEO_COUNTRY_CODE"] = "DE"
        request.META["HTTP_X_CLIENT_GEO_COUNTRY_NAME"] = "Germany"
        result = geoip(request)
        self.assertEqual(result["GEO_COUNTRY_CODE"], "DE")
        self.assertEqual(result["GEO_COUNTRY_NAME"], "Germany")

    def test_geo_headers_absent(self):
        rf = RequestFactory()
        request = rf.get("/")
        result = geoip(request)
        self.assertEqual(result["GEO_COUNTRY_CODE"], "")
        self.assertEqual(result["GEO_COUNTRY_NAME"], "")
