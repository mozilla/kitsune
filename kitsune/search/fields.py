from functools import partial

from django.conf import settings
from elasticsearch_dsl.field import Keyword
from elasticsearch_dsl.field import Object as DSLObject
from elasticsearch_dsl.field import Text

from kitsune.search.es_utils import es_analyzer_for_locale

SUPPORTED_LANGUAGES = list(settings.SUMO_LANGUAGES)
# this is a test locale - no need to add it to ES
SUPPORTED_LANGUAGES.remove("xx")


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
