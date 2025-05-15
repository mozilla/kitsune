from django.conf import settings
from django.test import TestCase

from kitsune.search import es_utils
from kitsune.search.base import SumoDocument
from kitsune.search.es_compat import setup_elasticsearch_modules


class SearchBasicsTestCase(TestCase):
    """Basic tests for the search app functionality."""

    def test_es_version_setting_is_set(self):
        """Test that the ES_VERSION setting is set correctly."""
        self.assertIn("ES_VERSION", dir(settings))
        self.assertIsNotNone(settings.ES_VERSION)
        self.assertIn(settings.ES_VERSION, [7, 8])

    def test_es_client_initialization(self):
        """Test that the ES client can be initialized."""
        client = es_utils.es_client()
        self.assertIsNotNone(client)

        # Basic client functionality test
        # This should not raise an exception if the client is properly initialized
        try:
            info = client.info()
            self.assertIsNotNone(info)
        except Exception as e:
            self.fail(f"ES client initialization failed with error: {e}")

    def test_es_search_migration(self):
        """Test that document migration works."""
        # Get all document types
        doc_types = es_utils.get_doc_types()
        self.assertTrue(len(doc_types) > 0, "No document types found")

        # Verify all document types inherit from SumoDocument
        for doc_type in doc_types:
            self.assertTrue(issubclass(doc_type, SumoDocument))

            # Test that index name and aliases are set up correctly
            self.assertTrue(hasattr(doc_type.Index, "base_name"))
            self.assertTrue(hasattr(doc_type.Index, "read_alias"))
            self.assertTrue(hasattr(doc_type.Index, "write_alias"))

    def test_es_module_setup(self):
        """Test that ES module setup works correctly."""
        # The setup_elasticsearch_modules function should run without exceptions
        try:
            setup_elasticsearch_modules()
        except Exception as e:
            self.fail(f"ES module setup failed with error: {e}")
