import importlib
import inspect
from hashlib import shake_128
import json

from celery import task
from django.conf import settings
from elasticsearch7.helpers import bulk as es7_bulk
from elasticsearch_dsl import Document, UpdateByQuery, analyzer, token_filter, char_filter

from kitsune.search import config
from kitsune.search.v2 import elasticsearch7


def _insert_custom_filters(locale, filter_list, char=False):
    """
    Takes a list containing in-built filters (as strings), and the settings for custom filters
    (as dicts). Turns the dicts into instances of `token_filter` or `char_filter` depending
    on the value of the `char` argument.
    """

    def mapping_func(filter):
        if type(filter) is dict:
            # sort filter dict by keys, so reordering doesn't change hash
            sorted_filter = {key: filter[key] for key in sorted(filter)}
            # hash to prevent collisions between filters of the same type in a locale
            hashed_filter = shake_128(json.dumps(sorted_filter).encode("utf-8")).hexdigest(2)
            name = f'{locale}_{filter["type"]}_{hashed_filter}'
            if char:
                return char_filter(name, **filter)
            return token_filter(name, **filter)
        return filter

    return list(map(mapping_func, filter_list))


def _get_locale_specific_analyzer(locale):
    """Get an analyzer for locales specified in config otherwise return `None`"""

    locale_analyzer = config.ES_LOCALE_ANALYZERS.get(locale)

    if not locale_analyzer:
        return None

    if locale_analyzer.get("plugin") and not settings.ES_USE_PLUGINS:
        return None

    # use default values from ES_DEFAULT_ANALYZER if not overridden
    locale_analyzer = config.ES_DEFAULT_ANALYZER | locale_analyzer

    # turn dictionaries into `char_filter` and `token_filter` instances
    locale_analyzer["filter"] = _insert_custom_filters(locale, locale_analyzer["filter"])
    locale_analyzer["char_filter"] = _insert_custom_filters(
        locale, locale_analyzer["char_filter"], char=True
    )

    return analyzer(
        locale,
        tokenizer=locale_analyzer["tokenizer"],
        filter=locale_analyzer["filter"],
        char_filter=locale_analyzer["char_filter"],
    )


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
    return analyzer(
        "default_sumo",
        tokenizer=config.ES_DEFAULT_ANALYZER["tokenizer"],
        filter=config.ES_DEFAULT_ANALYZER["filter"],
        char_filter=config.ES_DEFAULT_ANALYZER["char_filter"],
    )


def es7_client(**kwargs):
    """Return an ES7 Elasticsearch client"""
    # prefer a cloud_id if available
    if es7_cloud_id := settings.ES7_CLOUD_ID:
        kwargs.update({"cloud_id": es7_cloud_id, "http_auth": settings.ES7_HTTP_AUTH})
    else:
        kwargs.update({"hosts": settings.ES7_URLS})
    return elasticsearch7.Elasticsearch(**kwargs)


def get_doc_types(paths=["kitsune.search.v2.documents"]):
    """Return all registered document types"""

    doc_types = []
    modules = [importlib.import_module(path) for path in paths]

    for module in modules:
        for key in dir(module):
            cls = getattr(module, key)
            if (
                inspect.isclass(cls)
                and issubclass(cls, Document)
                and cls != Document
                and cls.__name__ != "SumoDocument"
            ):
                doc_types.append(cls)
    return doc_types


@task
def index_object(doc_type_name, obj_id):
    """Index an ORM object given an object id and a document type name."""

    doc_type = next(cls for cls in get_doc_types() if cls.__name__ == doc_type_name)
    model = doc_type.get_model()

    try:
        obj = model.objects.get(pk=obj_id)
    except model.DoesNotExist:
        # if the row doesn't exist in DB, it may have been deleted while this job
        # was in the celery queue - this shouldn't be treated as a failure, so
        # just return
        return

    if doc_type.update_document:
        doc_type.prepare(obj).to_action("update", doc_as_upsert=True)
    else:
        doc_type.prepare(obj).to_action("index")


@task
def index_objects_bulk(doc_type_name, obj_ids, timeout=settings.ES_BULK_DEFAULT_TIMEOUT):
    """Bulk index ORM objects given a list of object ids and a document type name."""

    doc_type = next(cls for cls in get_doc_types() if cls.__name__ == doc_type_name)

    objects = doc_type.get_queryset().filter(pk__in=obj_ids)
    # prepare the docs for indexing
    docs = [doc_type.prepare(obj) for obj in objects]
    # set the appropriate action per document type
    action = "index"
    kwargs = {}
    # If the `update_document` is true we are using update instead of index
    if doc_type.update_document:
        action = "update"
        kwargs.update({"doc_as_upsert": True})

    # if the request doesn't resolve within `timeout`,
    # sleep for `timeout` then try again up to `settings.ES_BULK_MAX_RETRIES` times,
    # before raising an exception:
    es7_bulk(
        es7_client(
            timeout=timeout,
            retry_on_timeout=True,
            initial_backoff=timeout,
            max_retries=settings.ES_BULK_MAX_RETRIES,
        ),
        (doc.to_action(action=action, is_bulk=True, **kwargs) for doc in docs),
    )


@task
def remove_from_field(doc_type_name, field_name, field_value):
    """Remove a value from all documents in the doc_type's index."""
    doc_type = next(cls for cls in get_doc_types() if cls.__name__ == doc_type_name)

    script = (
        f"if (ctx._source.{field_name}.contains(params.value)) {{"
        f"ctx._source.{field_name}.remove(ctx._source.{field_name}.indexOf(params.value))"
        f"}}"
    )

    update = UpdateByQuery(using=es7_client(), index=doc_type._index._name)
    update = update.filter("term", **{field_name: field_value})
    update = update.script(source=script, params={"value": field_value}, conflicts="proceed")

    # refresh index to ensure search fetches all matches
    doc_type._index.refresh()

    update.execute()


@task
def delete_object(doc_type_name, obj_id):
    """Unindex an ORM object given an object id and document type name."""

    doc_type = next(cls for cls in get_doc_types() if cls.__name__ == doc_type_name)
    doc = doc_type()
    doc.meta.id = obj_id
    doc.to_action("delete")
