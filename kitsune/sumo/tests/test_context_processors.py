from nose.tools import eq_
from test_utils import RequestFactory

from kitsune.sumo.tests import TestCase
from kitsune.sumo.context_processors import geoip_cache_detector


class TestGeoipCacheDetector(TestCase):

    def test_cache_when_no_cookie(self):
        """GeoIP code is included when there are no cookies."""
        req = RequestFactory()
        val = geoip_cache_detector(req)
        eq_(val['include_geoip'], True)

    def test_when_both(self):
        """GeoIP code is not included when both name and code already exist."""
        req = RequestFactory()
        req.COOKIES = {
            'geoip_country_name': 'United States',
            'geoip_country_code': 'US',
        }
        val = geoip_cache_detector(req)
        eq_(val['include_geoip'], False)

    def test_only_name(self):
        """GeoIP code is included when the country code is missing."""
        req = RequestFactory()
        req.COOKIES = {
            'geoip_country_name': 'United States',
        }
        val = geoip_cache_detector(req)
        eq_(val['include_geoip'], True)

    def test_only_code(self):
        """GeoIP code is included when the country name is missing."""
        req = RequestFactory()
        req.COOKIES = {
            'geoip_country_code': 'US',
        }
        val = geoip_cache_detector(req)
        eq_(val['include_geoip'], True)

    def test_english(self):
        """GepIP code is included when the locale is en-US."""
        req = RequestFactory()
        req.LANGUAGE_CODE = 'en-US'
        val = geoip_cache_detector(req)
        eq_(val['include_geoip'], True)

    def test_german(self):
        """GepIP code is not included when the locale is de."""
        req = RequestFactory()
        req.LANGUAGE_CODE = 'de'
        val = geoip_cache_detector(req)
        eq_(val['include_geoip'], False)
