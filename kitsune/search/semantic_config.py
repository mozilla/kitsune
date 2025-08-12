"""
Configuration for semantic search using Elasticsearch E5 multilingual model.

This module contains settings for configuring semantic search with E5,
Elasticsearch's multilingual text embedding model.
"""

from django.conf import settings

# E5 Multilingual Model Configuration for Semantic Search
E5_MODELS = {
    '.multilingual-e5-small-elasticsearch': {
        'description': 'E5 Small - Multilingual text embedding model',
        'type': 'e5',
        'version': 'small',
        'optimized_for': 'multilingual_search',
        'vector_type': 'dense',
        'languages': ['en', 'ar', 'bg', 'ca', 'cs', 'da', 'de', 'el', 'es', 'et', 'fa', 'fi', 'fr', 'gl', 'gu', 'he', 'hi', 'hr', 'hu', 'hy', 'id', 'it', 'ja', 'ka', 'ko', 'ku', 'lt', 'lv', 'mk', 'mn', 'mr', 'ms', 'my', 'nb', 'nl', 'pl', 'pt', 'ro', 'ru', 'sk', 'sl', 'sq', 'sr', 'sv', 'th', 'tr', 'uk', 'ur', 'vi', 'zh'],
        'use_case': 'Multilingual semantic search with good performance/size balance'
    },
    '.multilingual-e5-base-elasticsearch': {
        'description': 'E5 Base - Multilingual text embedding model (larger, more accurate)',
        'type': 'e5',
        'version': 'base',
        'optimized_for': 'multilingual_search',
        'vector_type': 'dense',
        'languages': ['en', 'ar', 'bg', 'ca', 'cs', 'da', 'de', 'el', 'es', 'et', 'fa', 'fi', 'fr', 'gl', 'gu', 'he', 'hi', 'hr', 'hu', 'hy', 'id', 'it', 'ja', 'ka', 'ko', 'ku', 'lt', 'lv', 'mk', 'mn', 'mr', 'ms', 'my', 'nb', 'nl', 'pl', 'pt', 'ro', 'ru', 'sk', 'sl', 'sq', 'sr', 'sv', 'th', 'tr', 'uk', 'ur', 'vi', 'zh'],
        'use_case': 'High-quality multilingual semantic search with better accuracy'
    }
}

# Default model - E5 Small is ideal for multilingual search with good performance
DEFAULT_EMBEDDING_MODEL = getattr(
    settings,
    'ELASTICSEARCH_SEMANTIC_MODEL_ID',
    '.multilingual-e5-small-elasticsearch'
)


def get_e5_model_config(model_id=None):
    """
    Get configuration for E5 model.

    Args:
        model_id (str): The model identifier. If None, uses DEFAULT_EMBEDDING_MODEL.

    Returns:
        dict: Model configuration including type and description.
    """
    model_id = model_id or DEFAULT_EMBEDDING_MODEL
    return E5_MODELS.get(model_id, E5_MODELS['.multilingual-e5-small-elasticsearch'])


def get_supported_e5_models():
    """Get list of supported E5 models."""
    return list(E5_MODELS.keys())


def get_semantic_search_config():
    """
    Get the E5 multilingual semantic search configuration.

    Returns:
        dict: Configuration dictionary with E5 settings.
    """
    return {
        'default_model': DEFAULT_EMBEDDING_MODEL,
        'model_config': get_e5_model_config(),
        'supported_models': list(E5_MODELS.keys()),
        'multilingual_support': True,
        'vector_type': 'dense',
        'search_type': 'multilingual_semantic'
    }
