from datetime import datetime

from django.conf import settings
from django.template.defaultfilters import slugify
from django.test import override_settings

from kitsune.sumo.tests import LocalizingClient
from kitsune.sumo.tests import TestCase


# Override the cache prefix with a test-specific one.
@override_settings(
    CACHE_PREFIX=getattr(settings, "CACHE_PREFIX", None) or "" + "test" + slugify(datetime.now())
)
class TestCaseBase(TestCase):
    """Base TestCase for the flagit app test cases."""

    client_class = LocalizingClient
