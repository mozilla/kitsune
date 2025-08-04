from functools import partial

from django.conf import settings
from elasticsearch.dsl import Keyword, Text, field
from elasticsearch.dsl import Object as DSLObject

from kitsune.search.es_utils import es_analyzer_for_locale

SUPPORTED_LANGUAGES = list(settings.SUMO_LANGUAGES)
# this is a test locale - no need to add it to ES
SUPPORTED_LANGUAGES.remove("xx")

# Default E5 multilingual model
DEFAULT_E5_MODEL = getattr(settings, 'ELASTICSEARCH_SEMANTIC_MODEL_ID', '.multilingual-e5-small')


def SemanticTextField(**params):
    """
    Create a semantic_text field for E5 multilingual semantic search.

    Args:
        **params: Additional parameters for the field

    Returns:
        field.SemanticText: Configured semantic text field for E5 multilingual model
    """
    return field.SemanticText(inference_id=DEFAULT_E5_MODEL, **params)


def _get_fields(field, locales, **params):
    """Construct the sub-fields of locale aware multi-field"""
    data = {}

    for locale in locales:
        if field is Text:
            analyzer = es_analyzer_for_locale(locale)
            search_analyzer = es_analyzer_for_locale(locale, search_analyzer=True)
            field_obj = field(
                analyzer=analyzer,
                search_analyzer=search_analyzer,
                search_quote_analyzer=analyzer,
                **params,
            )
        else:
            field_obj = field(**params)
        data[locale] = field_obj

    return data


def construct_locale_field(field, locales, **params):
    """Construct a locale aware object."""
    inner_fields = _get_fields(locales=locales, field=field, **params)
    return DSLObject(properties=inner_fields)


SumoTextField = partial(construct_locale_field, field=Text)
SumoKeywordField = partial(construct_locale_field, field=Keyword)
# This is an object in the form of
# {'en-US': Text(analyzer_for_the_specific_locale)}
SumoLocaleAwareTextField = partial(SumoTextField, locales=SUPPORTED_LANGUAGES)
SumoLocaleAwareKeywordField = partial(SumoKeywordField, locales=SUPPORTED_LANGUAGES)


# Semantic text field for multi-language support with E5 multilingual model
def SumoLocaleAwareSemanticTextField(**params):
    """
    Create a locale-aware semantic text field using E5 multilingual model.

    This creates an object field with semantic_text subfields for each supported locale,
    all using E5 multilingual model for semantic search.

    Args:
        **params: Additional parameters for each semantic text field

    Returns:
        DSLObject: Object field containing E5 semantic text fields for each locale
    """
    inner_fields = {}
    for locale in SUPPORTED_LANGUAGES:
        inner_fields[locale] = field.SemanticText(inference_id=DEFAULT_E5_MODEL, **params)

    return DSLObject(properties=inner_fields)
