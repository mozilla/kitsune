from django.test.utils import override_settings
from kitsune.sumo.tests import TestCase


@override_settings(ES_LIVE_INDEXING=True)
class Elastic7TestCase(TestCase):
    """Base class for Elastic Search 7 tests, providing some conveniences"""

    search_v2_tests = True
