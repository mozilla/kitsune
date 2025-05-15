from unittest.mock import patch, MagicMock

from django.test import TestCase

from kitsune.search.base import SumoDocument


# Test document classes
class TestDocument(SumoDocument):
    """Test document class for testing SumoDocument functionality."""

    class Index:
        pass


class SubTestDocument(TestDocument):
    """Subclass of test document to test inheritance."""

    class Index:
        pass


class SumoDocumentTestCase(TestCase):
    """Tests for SumoDocument functionality."""

    def test_document_index_setup(self):
        """Test that document indices are set up correctly."""
        # Test base class
        self.assertTrue(hasattr(TestDocument.Index, "base_name"))
        self.assertTrue(hasattr(TestDocument.Index, "read_alias"))
        self.assertTrue(hasattr(TestDocument.Index, "write_alias"))

        # Base name should match class name
        self.assertIn("testdocument", TestDocument.Index.base_name)
        # Read alias should be derived from base name
        self.assertEqual(TestDocument.Index.read_alias, f"{TestDocument.Index.base_name}_read")
        # Write alias should be derived from base name
        self.assertEqual(TestDocument.Index.write_alias, f"{TestDocument.Index.base_name}_write")

        # For subclass, base name should match parent class name
        self.assertIn("testdocument", SubTestDocument.Index.base_name)
        self.assertEqual(SubTestDocument.Index.base_name, TestDocument.Index.base_name)

    def test_document_search_method(self):
        """Test that the search method uses the read alias."""
        search = TestDocument.search()
        self.assertEqual(search._index, [TestDocument.Index.read_alias])

    @patch("kitsune.search.base.es_client")
    def test_document_migrate_writes(self, mock_es_client):
        """Test that migrate_writes creates a new index and updates the write alias."""
        # Mock client and return values
        mock_client = MagicMock()
        mock_es_client.return_value = mock_client

        # Mock init method to avoid creating actual index
        with patch.object(TestDocument, "init") as mock_init:
            TestDocument.migrate_writes()

            # Should call init once with an index name
            mock_init.assert_called_once()
            index_name = mock_init.call_args[1]["index"]
            self.assertIsNotNone(index_name)

            # Should call _update_alias with write alias and new index name
            with patch.object(TestDocument, "_update_alias") as mock_update_alias:
                TestDocument.migrate_writes()
                mock_update_alias.assert_called_once_with(
                    TestDocument.Index.write_alias, mock_init.call_args[1]["index"]
                )

    @patch("kitsune.search.base.es_client")
    def test_document_migrate_reads(self, mock_es_client):
        """Test that migrate_reads updates the read alias to point to
        the same index as write alias."""
        # Mock client and alias_points_at
        mock_client = MagicMock()
        mock_es_client.return_value = mock_client

        with patch.object(
            TestDocument, "alias_points_at", return_value="test-index"
        ) as mock_alias_points_at:
            with patch.object(TestDocument, "_update_alias") as mock_update_alias:
                TestDocument.migrate_reads()

                # Should call alias_points_at with write alias
                mock_alias_points_at.assert_called_once_with(TestDocument.Index.write_alias)

                # Should call _update_alias with read alias and index returned by alias_points_at
                mock_update_alias.assert_called_once_with(
                    TestDocument.Index.read_alias, "test-index"
                )
