from django.test.utils import override_settings

from kitsune.search.es7_utils import get_doc_types
from kitsune.sumo.tests import TestCase


@override_settings(ES_LIVE_INDEXING=True)
class Elastic7TestCase(TestCase):
    """Base class for Elastic Search 7 tests, providing some conveniences"""

    def refresh(self):
        """Refresh ES7 indices."""

        for doc_type in get_doc_types():
            doc_type._index.refresh()
