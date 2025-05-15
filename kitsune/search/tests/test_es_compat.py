from django.test import TestCase

from kitsune.search.es_compat import (
    CompatResponse,
    normalize_response,
    setup_elasticsearch_modules,
    ApiError,
    TransportError,
    NotFoundError,
    RequestError,
)


class ESCompatTestCase(TestCase):
    """Tests for the ES compatibility layer."""

    def test_compat_response_dict(self):
        """Test that CompatResponse handles dict responses correctly."""
        # Test with ES7-style dict response
        test_dict = {"key": "value", "nested": {"subkey": "subvalue"}}
        resp = CompatResponse(test_dict)

        # Check properties
        self.assertEqual(resp.body, test_dict)
        self.assertIsNone(resp.meta)

        # Check dict-like behavior
        self.assertEqual(resp["key"], "value")
        self.assertEqual(resp["nested"]["subkey"], "subvalue")
        self.assertTrue("key" in resp)
        self.assertEqual(resp.get("key"), "value")
        self.assertEqual(resp.get("missing", "default"), "default")

        # Test iteration and dict methods
        self.assertEqual(set(resp.keys()), set(test_dict.keys()))
        self.assertEqual(dict(resp.items()), test_dict)

        # Can't use set() with values that contain dictionaries (unhashable)
        # Compare values directly instead
        self.assertEqual(list(resp.values()), list(test_dict.values()))

        # Test copy
        self.assertEqual(resp.copy(), test_dict)

    def test_normalize_response_decorator(self):
        """Test that normalize_response decorator wraps responses correctly."""
        test_dict = {"result": "success"}

        # Create a test function with the decorator
        @normalize_response
        def test_func():
            return test_dict

        # Call the decorated function
        result = test_func()

        # Verify it returns a response with the correct behavior, without using isinstance
        # which can fail if the module is reloaded
        self.assertTrue(hasattr(result, "body"))
        self.assertEqual(result.body, test_dict)
        self.assertEqual(result["result"], "success")

    def test_exception_classes_defined(self):
        """Test that exception classes are properly defined after setup."""
        # After setup_elasticsearch_modules is called, these should be defined
        setup_elasticsearch_modules()

        # Verify exception classes are defined
        self.assertTrue(ApiError is not None)
        self.assertTrue(TransportError is not None)
        self.assertTrue(NotFoundError is not None)
        self.assertTrue(RequestError is not None)
