import importlib
import inspect

from django.conf import settings

from celery import task
from elasticsearch_dsl import token_filter, analyzer, Document

from kitsune.search import config
from kitsune.search.v2 import elasticsearch7


def _get_locale_specific_analyzer(locale):
    """Get an analyzer for locales specified in config otherwise return `None`"""

    locale_analyzer = config.ES_LOCALE_ANALYZERS.get(locale)
    if locale_analyzer:
        if not settings.ES_USE_PLUGINS and locale_analyzer in settings.ES_PLUGIN_ANALYZERS:
            return None

        return analyzer(locale, type=locale_analyzer)

    snowball_language = config.ES_SNOWBALL_LOCALES.get(locale)
    if snowball_language:
        # The locale is configured to use snowball filter
        token_name = 'snowball_{}'.format(locale.lower())
        snowball_filter = token_filter(token_name, type='snowball', language=snowball_language)

        # Use language specific snowball filter with standard analyzer.
        # The standard analyzer is basically a analyzer with standard tokenizer
        # and standard, lowercase and stop filter
        locale_analyzer = analyzer(locale, tokenizer='standard',
                                   filter=['lowercase', 'stop', snowball_filter])
        return locale_analyzer


def es_analyzer_for_locale(locale):
    """Pick an appropriate analyzer for a given locale.
    If no analyzer is defined for `locale` or the locale analyzer uses a plugin
    but using plugin is turned off from settings, return ES analyzer named "standard".
    """

    local_specific_analyzer = _get_locale_specific_analyzer(locale=locale)

    if local_specific_analyzer:
        return local_specific_analyzer

    # No specific analyzer found for the locale
    # So use the standard analyzer as default
    return analyzer('default_sumo', tokenizer='standard', filter=['lowercase'])


def es7_client():
    """Return an ES7 Elasticsearch client"""
    return elasticsearch7.Elasticsearch(settings.ES7_URLS)


def get_doc_types(paths=['kitsune.search.v2.documents']):
    """Return all registered document types"""

    doc_types = []
    modules = [importlib.import_module(path) for path in paths]

    for module in modules:
        for key in dir(module):
            cls = getattr(module, key)
            if inspect.isclass(cls) and issubclass(cls, Document) and cls != Document:
                doc_types.append(cls)
    return doc_types


@task
def index_object(doc_type_name, obj_id):
    """Index an ORM object given an object id and a document type name."""

    doc_type = next(cls for cls in get_doc_types() if cls.__name__ == doc_type_name)
    model = doc_type.get_model()

    obj = model.objects.get(id=obj_id)
    doc = doc_type.prepare(obj)
    doc.save()
