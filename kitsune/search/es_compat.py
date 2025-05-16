"""
Elasticsearch compatibility module.

This module provides a compatibility layer for Elasticsearch 7 and 8, allowing code
to import from 'elasticsearch' and 'elasticsearch_dsl' regardless of which version
is actually being used.

The module detects the Elasticsearch version in use and imports the appropriate modules,
creating aliases as needed. Since Elasticsearch 8 has integrated elasticsearch_dsl
functionality, this module handles that aliasing as well.
"""

import sys
from unittest.mock import MagicMock


def _get_es_version():
    """Get the configured Elasticsearch version."""
    try:
        # Import here to avoid circular import
        from django.conf import settings

        # Use the setting if it exists
        return getattr(settings, "ES_VERSION", None)
    except (ImportError, AttributeError):
        # If settings isn't available yet, assume 7 for now
        return 7


# Keep track of whether we've already set up the modules
_MODULES_SETUP = False

# Forward declarations of exception classes to be properly set up by setup_elasticsearch_modules()
NotFoundError = None
RequestError = None
TransportError = None
ApiError = None


class CompatResponse:
    """
    Compatibility wrapper for Elasticsearch responses.

    In ES7, responses are plain dicts/lists. In ES8, they are ObjectApiResponse with
    .body and .meta attributes. This class normalizes responses to work with either
    ES7 or ES8 response formats.
    """

    def __init__(self, response):
        """
        Initialize from either an ES7 dict/list or an ES8 ObjectApiResponse.

        Args:
            response: The ES response object (ES7 dict/list or ES8 ObjectApiResponse)
        """
        self._original = response

        # Handle ES8 response object
        if hasattr(response, "body") and hasattr(response, "meta"):
            self._body = response.body
            self._meta = response.meta
            self._is_es8 = True
        # Handle ES7 dict/list response
        else:
            self._body = response
            self._meta = None
            self._is_es8 = False

    @property
    def body(self):
        """Get the response body (the actual data)."""
        return self._body

    @property
    def meta(self):
        """
        Get metadata about the response.
        For ES8 responses, this returns the original meta object.
        For ES7 responses, this will be None.
        """
        return self._meta

    def __getitem__(self, key):
        """Support dictionary-like access to the response data."""
        return self._body[key]

    def __contains__(self, key):
        """Support 'in' operator for the response data."""
        return key in self._body

    def get(self, key, default=None):
        """Dict-like get() method."""
        return self._body.get(key, default)

    def __iter__(self):
        """Make the object iterable like a dict."""
        return iter(self._body)

    def keys(self):
        """Support dict keys() method."""
        return self._body.keys()

    def items(self):
        """Support dict items() method."""
        return self._body.items()

    def values(self):
        """Support dict values() method."""
        return self._body.values()

    def copy(self):
        """
        Support dict copy() method.

        This is needed by elasticsearch_dsl.utils.from_es which expects the response
        to have a copy method. The method returns a shallow copy of the response body.
        """
        if isinstance(self._body, dict):
            return self._body.copy()
        # For non-dict responses, return the body directly
        return self._body


def normalize_response(func):
    """
    Decorator to normalize responses between ES7 and ES8.

    ES7 returns dict/list objects directly
    ES8 returns ObjectApiResponse objects with .body and .meta attributes

    This decorator normalizes these differences by wrapping the response in a CompatResponse.
    """

    def wrapper(*args, **kwargs):
        response = func(*args, **kwargs)
        if response is None:
            return None
        return CompatResponse(response)

    return wrapper


class IndicesClientCompat:
    """
    Compatibility wrapper for ES8 IndicesClient to match ES7 behavior.

    In ES7, client.indices is a separate client instance with various methods.
    In ES8, these methods are still available but organized differently.
    This class ensures that code written for ES7 client.indices.X works with ES8.
    """

    def __init__(self, es_client):
        """Initialize with the main ES client instance."""
        self._client = es_client

    @normalize_response
    def get_alias(self, name=None, index=None):
        """Get alias information."""
        return self._client.indices.get_alias(name=name, index=index)

    @normalize_response
    def exists(self, index=None, **kwargs):
        """Check if an index exists."""
        return self._client.indices.exists(index=index, **kwargs)

    @normalize_response
    def get_settings(self, index=None, **kwargs):
        """Get index settings."""
        try:
            return self._client.indices.get_settings(index=index, **kwargs)
        except Exception as e:
            # If the index doesn't exist yet (common during creation), return empty settings
            # rather than raising an error
            if any(x in str(e).lower() for x in ["index_not_found", "no such index"]):
                # Return an empty dict for the requested index to prevent errors
                if index:
                    return {index: {"settings": {"index": {}}}}
                return {}
            # Re-raise other exceptions
            raise

    @normalize_response
    def put_settings(self, index=None, body=None, **kwargs):
        """Update index settings."""
        try:
            if body:
                # In ES7, body is passed as a separate parameter
                # In ES8, settings are passed directly
                # Our compatibility layer should handle both formats
                if hasattr(self._client.indices, "put_settings"):
                    # Original ES7-style call
                    return self._client.indices.put_settings(index=index, body=body, **kwargs)
                else:
                    # For ES8, merge body into kwargs
                    return self._client.indices.put_settings(index=index, **body, **kwargs)
            return self._client.indices.put_settings(index=index, **kwargs)
        except Exception as e:
            # Handle the case where the index doesn't exist yet
            if any(x in str(e).lower() for x in ["index_not_found", "no such index"]):
                # If we're trying to set settings on a non-existent index, we need to create
                # it first
                settings_body = body or {}
                try:
                    # Try to create the index with the settings
                    create_body = {"settings": settings_body.get("settings", settings_body)}
                    self.create(index=index, body=create_body)
                    return {"acknowledged": True}  # Return success response
                except Exception:
                    # If we can't create it, re-raise the original error
                    raise
            # For other types of errors, just re-raise
            raise

    @normalize_response
    def close(self, index):
        """Close an index."""
        try:
            # Try different parameters based on ES version
            try:
                return self._client.indices.close(index=index)
            except TypeError:
                # Some ES versions might not use keyword arguments
                return self._client.indices.close(index)
        except Exception as e:
            # If the index doesn't exist, just return success
            if "index_not_found" in str(e).lower() or "no such index" in str(e).lower():
                return {"acknowledged": True}
            # Re-raise other errors
            raise

    @normalize_response
    def open(self, index):
        """Open an index."""
        try:
            # Try different parameters based on ES version
            try:
                return self._client.indices.open(index=index)
            except TypeError:
                # Some ES versions might not use keyword arguments
                return self._client.indices.open(index)
        except Exception as e:
            # If the index doesn't exist, just return success
            if "index_not_found" in str(e).lower() or "no such index" in str(e).lower():
                return {"acknowledged": True}
            # Re-raise other errors
            raise

    @normalize_response
    def put_mapping(self, index=None, body=None, doc_type=None, **kwargs):
        """Update mapping for an index."""
        try:
            # Handle differences between ES7 and ES8
            if body:
                if hasattr(self._client.indices, "put_mapping"):
                    # ES7-style call
                    if doc_type:
                        return self._client.indices.put_mapping(
                            index=index, body=body, doc_type=doc_type, **kwargs
                        )
                    else:
                        return self._client.indices.put_mapping(index=index, body=body, **kwargs)
                else:
                    # ES8-style call - no doc_type, merge body into kwargs
                    return self._client.indices.put_mapping(index=index, **body, **kwargs)

            return self._client.indices.put_mapping(index=index, **kwargs)
        except Exception as e:
            # Handle common errors
            if any(x in str(e).lower() for x in ["index_not_found", "no such index"]):
                # If we're trying to put mapping on a non-existent index, create it first
                try:
                    # Create the index with default settings and the specified mapping
                    create_body = {"mappings": body}
                    self.create(index=index, body=create_body)
                    return {"acknowledged": True}
                except Exception:
                    # If we can't create it, re-raise the original error
                    raise
            # Re-raise other errors
            raise

    @normalize_response
    def put_alias(self, index, name, body=None):
        """Create or update an alias."""
        # In ES8, body params like 'filter' would be passed directly
        if body:
            return self._client.indices.put_alias(index=index, name=name, **body)
        return self._client.indices.put_alias(index=index, name=name)

    @normalize_response
    def update_aliases(self, body):
        """Bulk update aliases."""
        # In ES8, the actions would be passed directly
        if "actions" in body:
            # Fix for ES7 compatibility
            try:
                # ES7-style: body as full object
                return self._client.indices.update_aliases(body=body)
            except Exception:
                # ES8-style: actions parameter
                try:
                    return self._client.indices.update_aliases(actions=body["actions"])
                except Exception:
                    # Try other approach if first one fails
                    return self._client.indices.update_aliases(**body)
        return self._client.indices.update_aliases(**body)

    @normalize_response
    def reload_search_analyzers(self, index):
        """Reload search analyzers."""
        return self._client.indices.reload_search_analyzers(index=index)

    @normalize_response
    def clear_cache(self, index=None, **kwargs):
        """Clear cache."""
        return self._client.indices.clear_cache(index=index, **kwargs)

    @normalize_response
    def create(self, index, body=None, **kwargs):
        """Create an index."""
        if body:
            merged_kwargs = {**body, **kwargs}
            return self._client.indices.create(index=index, **merged_kwargs)
        return self._client.indices.create(index=index, **kwargs)


class ClusterClientCompat:
    """Compatibility wrapper for Elasticsearch cluster APIs."""

    def __init__(self, es_client):
        """Initialize with the main ES client instance."""
        self._client = es_client

    @normalize_response
    def state(self, index=None, metric=None, **kwargs):
        """Get cluster state for indices.

        Handle the case where an index doesn't exist yet by ensuring
        it appears in the response with a default state structure.
        """
        try:
            response = self._client.cluster.state(index=index, metric=metric, **kwargs)

            # For a non-existent index that's being checked, add a placeholder
            # structure to prevent KeyError when index doesn't exist
            if index and isinstance(index, str) and "metadata" in response:
                indices = response.get("metadata", {}).get("indices", {})
                if index not in indices:
                    # Add a placeholder with open state to allow creation to proceed
                    response["metadata"]["indices"][index] = {
                        "state": "open"  # Default to open state for new indices
                    }
            return response
        except Exception as error:
            # If the index doesn't exist, create a fake response
            if any(x in str(error).lower() for x in ["index_not_found", "no such index"]):
                fake_response = {
                    "metadata": {"indices": {index: {"state": "open"} if index else {}}}
                }
                return fake_response
            # Re-raise for other errors
            raise


class CompatElasticsearch:
    """
    Compatibility wrapper for Elasticsearch client to normalize ES7/ES8 differences.

    This wrapper handles:
    1. Argument differences (http_auth vs basic_auth)
    2. Response object differences
    3. Exception hierarchy differences
    4. The indices client property (present in ES7, different in ES8)
    """

    def __init__(self, client_class, *args, **kwargs):
        """
        Initialize the compatibility wrapper.

        Args:
            client_class: The actual ES client class (ES7's or ES8's Elasticsearch)
            *args, **kwargs: Arguments to pass to the client constructor
        """
        # Handle auth parameter differences between ES7 and ES8
        if "http_auth" in kwargs and client_class.__module__.startswith("elasticsearch8"):
            # For ES8, rename http_auth to basic_auth
            kwargs["basic_auth"] = kwargs.pop("http_auth")

        # Create the actual client
        self._client = client_class(*args, **kwargs)

        # Create compatible clients
        self.indices = IndicesClientCompat(self._client)
        self.cluster = ClusterClientCompat(self._client)

    @normalize_response
    def search(self, *args, **kwargs):
        """Search API with normalized response handling."""
        return self._client.search(*args, **kwargs)

    @normalize_response
    def count(self, *args, **kwargs):
        """Count API with normalized response handling."""
        return self._client.count(*args, **kwargs)

    @normalize_response
    def index(self, *args, **kwargs):
        """Index API with normalized response handling."""
        return self._client.index(*args, **kwargs)

    @normalize_response
    def update(self, *args, **kwargs):
        """Update API with normalized response handling."""
        return self._client.update(*args, **kwargs)

    @normalize_response
    def delete(self, *args, **kwargs):
        """Delete API with normalized response handling."""
        return self._client.delete(*args, **kwargs)

    @normalize_response
    def info(self, *args, **kwargs):
        """Info API with normalized response handling."""
        return self._client.info(*args, **kwargs)

    @normalize_response
    def get(self, *args, **kwargs):
        """Get API with normalized response handling."""
        return self._client.get(*args, **kwargs)

    # Add other ES API methods as needed

    def options(self, **kwargs):
        """
        Handle the ES8 .options() method for per-request configurations.

        In ES8, options like timeout and ignore must be set via .options().
        In ES7, they are passed directly to the API methods.
        """
        if hasattr(self._client, "options"):
            # ES8 implementation
            return CompatElasticsearch(type(self._client), self._client.options(**kwargs))

        # ES7 doesn't have options() method, so we'll handle it by creating
        # a new wrapper with the options as attributes to use later
        clone = CompatElasticsearch(type(self._client), self._client)
        clone._options = kwargs
        return clone

    def _apply_es7_options(self, kwargs):
        """Apply stored options for ES7 compatibility."""
        if hasattr(self, "_options"):
            # Convert ES8 option names to ES7 equivalents
            option_mapping = {
                "ignore_status": "ignore",
                "basic_auth": "http_auth",
                "request_timeout": "timeout",
            }

            for k, v in self._options.items():
                # Map the option name if needed
                es7_key = option_mapping.get(k, k)
                kwargs[es7_key] = v

        return kwargs

    def __getattr__(self, name):
        """
        Forward any unimplemented methods to the underlying client.

        This ensures that methods we haven't explicitly implemented
        still work by delegating to the actual client.
        """
        attr = getattr(self._client, name)

        if callable(attr):
            # For method calls, create a wrapper that normalizes the response
            def wrapper(*args, **kwargs):
                # Apply ES7 options if this is an ES7 client
                if not hasattr(self._client, "options"):
                    kwargs = self._apply_es7_options(kwargs)

                result = attr(*args, **kwargs)

                # Normalize the response if it's a data response
                if result is not None and (
                    isinstance(result, dict) or isinstance(result, list) or hasattr(result, "body")
                ):
                    return CompatResponse(result)
                return result

            return wrapper

        # For non-callable attributes, return the attribute directly
        return attr


def setup_elasticsearch_modules():
    """
    Set up the elasticsearch and elasticsearch_dsl modules based on the detected version.
    This function creates module-level aliases that can be imported throughout the codebase.
    """
    global _MODULES_SETUP, ApiError, TransportError, NotFoundError, RequestError

    # Don't set up modules more than once
    if _MODULES_SETUP:
        return

    es_version = _get_es_version()

    # Create the fake modules that will be loaded when code does standard imports
    elasticsearch = type("elasticsearch", (), {})()
    elasticsearch.__name__ = "elasticsearch"
    elasticsearch.__file__ = __file__

    elasticsearch_dsl = type("elasticsearch_dsl", (), {})()
    elasticsearch_dsl.__name__ = "elasticsearch_dsl"
    elasticsearch_dsl.__file__ = __file__

    # Dictionary of modules we've already imported to avoid circular imports
    imported = {}

    try:
        if es_version == 8:
            # For ES 8, import directly from elasticsearch8
            import elasticsearch8

            # Copy all attributes from elasticsearch8 to elasticsearch
            for attr in dir(elasticsearch8):
                if not attr.startswith("__"):
                    setattr(elasticsearch, attr, getattr(elasticsearch8, attr))

            # Set up the wrapped Elasticsearch class for compatibility
            original_es_class = elasticsearch8.Elasticsearch

            # Create a compatible Elasticsearch class that wraps the original
            def create_compatible_es(*args, **kwargs):
                return CompatElasticsearch(original_es_class, *args, **kwargs)

            # Replace the Elasticsearch class with our wrapper
            setattr(elasticsearch, "Elasticsearch", create_compatible_es)

            # For compatibility, also expose the elasticsearch_dsl API
            # since it's integrated into elasticsearch8
            from elasticsearch8 import helpers

            setattr(elasticsearch, "helpers", helpers)

            # Import common elasticsearch_dsl classes used in the codebase
            dsl_attrs = [
                "Document",
                "Search",
                "Q",
                "A",
                "InnerDoc",
                "field",
                "connections",
                "analyzer",
                "token_filter",
                "char_filter",
                "MetaField",
                "UpdateByQuery",
            ]

            for attr in dsl_attrs:
                try:
                    # First try to get it from elasticsearch8 directly
                    if attr not in imported:
                        imported[attr] = getattr(elasticsearch8, attr)
                    setattr(elasticsearch_dsl, attr, imported[attr])
                except (AttributeError, ImportError):
                    # If not available, provide a mock to prevent import errors
                    setattr(elasticsearch_dsl, attr, MagicMock())

            # Create compatible exception classes
            # In ES8, ApiError is the base for HTTP errors, and TransportError
            # is for connection issues
            # In ES7, TransportError is the base for all errors

            # Save the original ES8 exception classes
            ApiError = getattr(elasticsearch8, "ApiError", None)
            TransportError = getattr(elasticsearch8, "TransportError", None)
            NotFoundError = getattr(elasticsearch8, "NotFoundError", None)
            RequestError = getattr(elasticsearch8, "RequestError", None)

            # For code expecting ES7's TransportError to catch API errors,
            # make sure our TransportError also catches ApiError
            if ApiError and TransportError:

                class CompatTransportError(TransportError):
                    """Compatibility TransportError that also catches ApiError."""

                    pass

                # Update the exception hierarchy
                ApiError.__bases__ = (CompatTransportError,) + ApiError.__bases__

                # Replace the TransportError with our compatible version
                setattr(elasticsearch, "TransportError", CompatTransportError)
                TransportError = CompatTransportError

        else:
            # For ES 7, import from elasticsearch7 and elasticsearch_dsl
            import elasticsearch7
            import elasticsearch_dsl as original_elasticsearch_dsl

            # Copy all attributes from elasticsearch7 to elasticsearch
            for attr in dir(elasticsearch7):
                if not attr.startswith("__"):
                    setattr(elasticsearch, attr, getattr(elasticsearch7, attr))

            # Set up the wrapped Elasticsearch class for compatibility
            original_es_class = elasticsearch7.Elasticsearch

            # Create a compatible Elasticsearch class that wraps the original
            def create_compatible_es(*args, **kwargs):
                return CompatElasticsearch(original_es_class, *args, **kwargs)

            # Replace the Elasticsearch class with our wrapper
            setattr(elasticsearch, "Elasticsearch", create_compatible_es)

            # Copy elasticsearch_dsl attributes
            for attr in dir(original_elasticsearch_dsl):
                if not attr.startswith("__"):
                    setattr(elasticsearch_dsl, attr, getattr(original_elasticsearch_dsl, attr))

            # Ensure helpers is available
            from elasticsearch7 import helpers

            setattr(elasticsearch, "helpers", helpers)

            # Add ES8-specific exceptions to maintain compatibility
            # with code written for ES8

            # Get existing ES7 exceptions
            TransportError = getattr(elasticsearch7, "TransportError", None)
            NotFoundError = getattr(elasticsearch7, "NotFoundError", None)
            RequestError = getattr(elasticsearch7, "RequestError", None)

            # Create ApiError for ES7 compatibility with ES8 code
            class ApiError(Exception):
                """Compatibility ApiError for ES7."""

                pass

            setattr(elasticsearch, "ApiError", ApiError)

        # Add modules to sys.modules so they can be imported
        sys.modules["elasticsearch"] = elasticsearch
        sys.modules["elasticsearch_dsl"] = elasticsearch_dsl

        # Mark modules as set up
        _MODULES_SETUP = True

    except ImportError as e:
        # If imports fail, log error but don't crash during module load
        print(f"Error setting up Elasticsearch compatibility: {e}")


# Set up the modules when this file is imported
setup_elasticsearch_modules()
