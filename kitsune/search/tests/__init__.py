from django.test.utils import override_settings

from kitsune.search.es_utils import get_doc_types
from kitsune.sumo.tests import TestCase


@override_settings(ES_LIVE_INDEXING=True)
class Elastic7TestCase(TestCase):
    """Base class for Elastic Search 7 tests, providing some conveniences"""

    def tearDown(self):
        """Delete all documents in each index."""
        for doc_type in get_doc_types():
            doc_type.search().query("match_all").delete()
            # specify a refresh operation on the index to update all shards
            # participated in the delete operation. This is different from
            # the API refresh=True which only updates the shard that performed
            # the specific delete/update/save op
            doc_type._index.refresh()
