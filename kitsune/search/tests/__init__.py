from django.test.utils import override_settings

from kitsune.search.es_utils import get_doc_types, es_client
from kitsune.sumo.tests import TestCase


@override_settings(ES_LIVE_INDEXING=True, TEST=True)
class ElasticTestCase(TestCase):
    """Base class for Elastic Search tests, providing some conveniences"""

    def setUp(self):
        """Set up test environment by ensuring clean indexes."""
        super().setUp()

        # Initialize indexes before tests if they don't exist
        client = es_client()
        for doc_type in get_doc_types():
            index_name = doc_type._index._name
            if not client.indices.exists(index=index_name):
                try:
                    doc_type.init()
                    # Force a refresh to ensure the index is ready
                    doc_type._index.refresh()
                except Exception as e:
                    self.fail(f"Failed to initialize index {index_name}: {e}")

        # Clean up indices before tests
        for doc_type in get_doc_types():
            try:
                # Delete all documents in the index without deleting the
                # index itself
                doc_type.search().query("match_all").delete()
                doc_type._index.refresh()
            except Exception as e:
                print(f"Error setting up ES index for {doc_type.__name__}: {e}")

    def tearDown(self):
        """Delete all documents in each index."""
        for doc_type in get_doc_types():
            try:
                # First refresh the index to ensure all operations are complete
                doc_type._index.refresh()

                # Delete all documents using query matching
                doc_type.search().query("match_all").delete()

                # Specify a refresh operation on the index to update all shards
                # participated in the delete operation. This is different from
                # the API refresh=True which only updates the shard that performed
                # the specific delete/update/save op
                doc_type._index.refresh()
            except Exception as e:
                print(f"Error cleaning up ES index for {doc_type.__name__}: {e}")

        super().tearDown()


# Keep backward compatibility with Elastic7TestCase name
Elastic7TestCase = ElasticTestCase
