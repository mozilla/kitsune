from datetime import UTC, datetime
from functools import cache

from django.test import tag
from django.test.utils import override_settings

from kitsune.search.es_utils import get_doc_types
from kitsune.sumo.tests import TestCase


@cache
@override_settings(ES_TIMEOUT=60)
def _initialize_indices():
    # Alias migrations use separate es_client() instances and need the setup budget too.
    timestamp = datetime.now(tz=UTC)
    for doc_type in get_doc_types():
        doc_type.migrate_writes(timestamp=timestamp)
        doc_type.migrate_reads()


@tag("es")
@override_settings(ES_LIVE_INDEXING=True)
class ElasticTestCase(TestCase):
    """Base class for Elastic Search tests, providing some conveniences"""

    @classmethod
    def setUpClass(cls):
        # Run once per process, only if an ES-backed test is actually selected.
        _initialize_indices()
        super().setUpClass()

    def tearDown(self):
        """Delete all documents in each index."""
        for doc_type in get_doc_types():
            doc_type.search().query("match_all").delete()
            # specify a refresh operation on the index to update all shards
            # participated in the delete operation. This is different from
            # the API refresh=True which only updates the shard that performed
            # the specific delete/update/save op
            doc_type._index.refresh()
