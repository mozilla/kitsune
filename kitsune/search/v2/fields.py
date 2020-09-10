from functools import partial

from django.conf import settings

from elasticsearch_dsl.field import Object as DSLObject
from elasticsearch_dsl.field import Text
from kitsune.search.v2.es7_utils import es_analyzer_for_locale


def _get_fields(field, locales, **params):
    """Construct the sub-fields of locale aware multi-field"""
    data = {}

    for locale in locales:
        analyzer = es_analyzer_for_locale(locale)
        field_obj = field(analyzer=analyzer, **params)
        data[locale] = field_obj

    return data


def construct_locale_field(field, locales, **params):
    """Construct a locale aware object."""
    inner_fields = _get_fields(locales=locales, field=field, **params)
    return DSLObject(properties=inner_fields)


SumoTextField = partial(construct_locale_field, field=Text)
# This is an object in the form of
# {'en-US': Text(analyzer_for_the_specific_locale)}
SumoLocaleAwareTextField = partial(SumoTextField, locales=settings.SUMO_LANGUAGES)
