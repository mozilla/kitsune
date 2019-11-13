from functools import partial

from django.conf import settings
from elasticsearch_dsl.field import Text, Keyword

from kitsune.search.v2.es7_utils import es_analyzer_for_locale


def _get_fields(field, locales, **params):
    """Construct the sub-fields of locale aware multi-field"""
    data = {}
    for locale in locales:
        analyzer = es_analyzer_for_locale(locale)
        field_obj = field(analyzer=analyzer, **params)
        data[locale] = field_obj

    return data


def construct_locale_field(locales, field, **params):
    """Construct a locale aware multi-field"""
    inner_fields = _get_fields(locales=locales, field=field, **params)
    return field(fields=inner_fields, **params)


LocaleField = construct_locale_field
LocaleText = partial(construct_locale_field, field=Text)
LocaleKeyword = partial(construct_locale_field, field=Keyword)
WikiLocaleText = partial(LocaleText, locales=settings.SUMO_LANGUAGES)
