from datetime import datetime

from django.conf import settings
from django.template.defaultfilters import slugify

from kitsune.sumo.tests import LocalizingClient, TestCase


class TestCaseBase(TestCase):
    """Base TestCase for the flagit app test cases."""

    client_class = LocalizingClient

    def setUp(self):
        """Setup"""
        # Change the CACHE_PREFIX to avoid conflicts
        self.orig_cache_prefix = getattr(settings, 'CACHE_PREFIX', None)
        settings.CACHE_PREFIX = (self.orig_cache_prefix or '' + 'test' +
                                 slugify(datetime.now()))

    def tearDown(self):
        settings.CACHE_PREFIX = self.orig_cache_prefix
