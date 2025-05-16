from django.test.utils import override_settings
from unittest.mock import patch, MagicMock

from kitsune.sumo.tests import TestCase


@override_settings(ES_LIVE_INDEXING=True)
class ElasticTestCase(TestCase):
    """Base class for Elasticsearch tests, compatible with both ES7 and ES8"""

    def setUp(self):
        """Set up mocks to prevent real Elasticsearch connections."""
        super().setUp()

        # Set up patchers
        self.patchers = []

        # Mock es_client to avoid real ES connections
        es_client_patcher = patch("kitsune.search.es_utils.es_client")
        self.mock_es_client = es_client_patcher.start()
        mock_client = MagicMock()

        # Add mock properties to the client
        mock_client.cluster = MagicMock()
        mock_client.indices = MagicMock()

        # Add a mock search method
        mock_client.search = MagicMock(return_value={"hits": {"hits": [], "total": {"value": 0}}})

        # Set up the indices.delete method to avoid actual index deletion
        mock_client.indices.delete = MagicMock(return_value={"acknowledged": True})

        # Return our mock client
        self.mock_es_client.return_value = mock_client
        self.patchers.append(es_client_patcher)

        # Mock other ES-related functionality to avoid real ES connections
        refresh_patcher = patch("elasticsearch_dsl.Index.refresh")
        self.mock_refresh = refresh_patcher.start()
        self.patchers.append(refresh_patcher)

        # Mock document search to avoid ES queries
        doc_search_patcher = patch("elasticsearch_dsl.Document.search")
        self.mock_doc_search = doc_search_patcher.start()
        mock_search = MagicMock()
        mock_search.query = MagicMock(return_value=mock_search)
        mock_search.delete = MagicMock(return_value={"deleted": 0})
        self.mock_doc_search.return_value = mock_search
        self.patchers.append(doc_search_patcher)

    def tearDown(self):
        """Clean up mocks."""
        # Stop all patchers
        for patcher in self.patchers:
            patcher.stop()
        super().tearDown()


# For backward compatibility
Elastic7TestCase = ElasticTestCase
