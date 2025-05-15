from unittest.mock import patch

from django.test import TestCase, override_settings

from kitsune.search import es_utils
from kitsune.search.base import SumoDocument


class ESUtilsTestCase(TestCase):
    """Tests for ES utility functions."""

    def test_es_analyzer_for_locale(self):
        """Test that es_analyzer_for_locale returns appropriate analyzers."""
        # Test with default locale
        analyzer = es_utils.es_analyzer_for_locale("en-US")
        self.assertIsNotNone(analyzer)

        # Test search analyzer
        search_analyzer = es_utils.es_analyzer_for_locale("en-US", search_analyzer=True)
        self.assertIsNotNone(search_analyzer)
        self.assertNotEqual(analyzer, search_analyzer)

        # Analyzer name should reflect locale
        self.assertIn("en-US", search_analyzer._name)

    def test_get_doc_types(self):
        """Test that get_doc_types returns document types."""
        doc_types = es_utils.get_doc_types()
        self.assertTrue(len(doc_types) > 0)

        # All should be subclasses of SumoDocument
        for doc_type in doc_types:
            self.assertTrue(issubclass(doc_type, SumoDocument))

    @patch("kitsune.search.es_utils.Elasticsearch")
    def test_es_client_params(self, mock_elasticsearch):
        """Test that es_client passes appropriate parameters to Elasticsearch."""
        # Test with cloud ID settings
        with override_settings(
            ES_CLOUD_ID="test-cloud-id", ES_HTTP_AUTH=("user", "pass"), ES_TIMEOUT=30
        ):
            es_utils.es_client()
            mock_elasticsearch.assert_called_once()
            args, kwargs = mock_elasticsearch.call_args
            self.assertEqual(kwargs.get("cloud_id"), "test-cloud-id")
            self.assertEqual(kwargs.get("http_auth"), ("user", "pass"))
            self.assertEqual(kwargs.get("timeout"), 30)

        # Reset mock
        mock_elasticsearch.reset_mock()

        # Test with URLs
        with override_settings(
            ES_CLOUD_ID=None, ES_URLS=["http://localhost:9200"], ES_TIMEOUT=30, ES_USE_SSL=True
        ):
            es_utils.es_client()
            mock_elasticsearch.assert_called_once()
            args, kwargs = mock_elasticsearch.call_args
            self.assertEqual(kwargs.get("hosts"), ["http://localhost:9200"])
            self.assertEqual(kwargs.get("timeout"), 30)
            self.assertEqual(kwargs.get("use_ssl"), True)
