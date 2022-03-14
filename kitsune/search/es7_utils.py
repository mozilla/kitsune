import importlib
import inspect

from celery import task
from django.conf import settings
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk as es7_bulk
from elasticsearch.helpers.errors import BulkIndexError
from elasticsearch_dsl import Document, UpdateByQuery, analyzer, char_filter, token_filter

from kitsune.search import config


def _insert_custom_filters(analyzer_name, filter_list, char=False):
    """
    Takes a list containing in-built filters (as strings), and the settings for custom filters
    (as dicts). Turns the dicts into instances of `token_filter` or `char_filter` depending
    on the value of the `char` argument.
    """

    def mapping_func(position_filter_tuple):
        position, filter = position_filter_tuple
        if type(filter) is dict:
            prefix = analyzer_name
            default_filters = config.ES_DEFAULT_ANALYZER["char_filter" if char else "filter"]
            if filter in default_filters:
                # detect if this filter exists in the default analyzer
                # if it does use the same name as the default
                # to avoid defining the same filter for each locale
                prefix = config.ES_DEFAULT_ANALYZER_NAME
                position = default_filters.index(filter)
            name = f'{prefix}_{position}_{filter["type"]}'
            if char:
                return char_filter(name, **filter)
            return token_filter(name, **filter)
        return filter

    return list(map(mapping_func, enumerate(filter_list)))


def _create_synonym_graph_filter(synonym_file_name):
    filter_name = f"{synonym_file_name}_synonym_graph"
    return token_filter(
        filter_name,
        type="synonym_graph",
        synonyms_path=f"synonyms/{synonym_file_name}.txt",
        # we must use "true" instead of True to work around an elastic-dsl bug
        expand="true",
        lenient="true",
        updateable="true",
    )


def es_analyzer_for_locale(locale, search_analyzer=False):
    """Pick an appropriate analyzer for a given locale.
    If no analyzer is defined for `locale` or the locale analyzer uses a plugin
    but using plugin is turned off from settings, return an analyzer named "default_sumo".
    """

    name = ""
    analyzer_config = config.ES_LOCALE_ANALYZERS.get(locale)

    if not analyzer_config or (analyzer_config.get("plugin") and not settings.ES_USE_PLUGINS):
        name = config.ES_DEFAULT_ANALYZER_NAME
        analyzer_config = {}

    # use default values from ES_DEFAULT_ANALYZER if not overridden
    # using python 3.9's dict union operator
    analyzer_config = config.ES_DEFAULT_ANALYZER | analyzer_config

    # turn dictionaries into `char_filter` and `token_filter` instances
    filters = _insert_custom_filters(name or locale, analyzer_config["filter"])
    char_filters = _insert_custom_filters(
        name or locale, analyzer_config["char_filter"], char=True
    )

    if search_analyzer:
        # create a locale-specific search analyzer, even if the index-time analyzer is
        # `sumo_default`. we do this so that we can adjust the synonyms used in any locale,
        # even if it doesn't have a custom analysis chain set up, without having to re-index
        name = locale + "_search_analyzer"
        filters.append(_create_synonym_graph_filter(config.ES_ALL_SYNONYMS_NAME))
        filters.append(_create_synonym_graph_filter(locale))

    return analyzer(
        name or locale,
        tokenizer=analyzer_config["tokenizer"],
        filter=filters,
        char_filter=char_filters,
    )


def es7_client(**kwargs):
    """Return an ES7 Elasticsearch client"""
    # prefer a cloud_id if available
    if es7_cloud_id := settings.ES7_CLOUD_ID:
        kwargs.update({"cloud_id": es7_cloud_id, "http_auth": settings.ES7_HTTP_AUTH})
    else:
        kwargs.update({"hosts": settings.ES7_URLS})
    return Elasticsearch(**kwargs)


def get_doc_types(paths=["kitsune.search.documents"]):
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
def index_objects_bulk(
    doc_type_name,
    obj_ids,
    timeout=settings.ES_BULK_DEFAULT_TIMEOUT,
    elastic_chunk_size=settings.ES_DEFAULT_ELASTIC_CHUNK_SIZE,
):
    """Bulk index ORM objects given a list of object ids and a document type name."""

    doc_type = next(cls for cls in get_doc_types() if cls.__name__ == doc_type_name)

    db_objects = doc_type.get_queryset().filter(pk__in=obj_ids)
    # prepare the docs for indexing
    docs = [doc_type.prepare(obj) for obj in db_objects]

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
    success, errors = es7_bulk(
        es7_client(
            timeout=timeout,
            retry_on_timeout=True,
            initial_backoff=timeout,
            max_retries=settings.ES_BULK_MAX_RETRIES,
        ),
        (doc.to_action(action=action, is_bulk=True, **kwargs) for doc in docs),
        chunk_size=elastic_chunk_size,
        raise_on_error=False,  # we'll raise the errors ourselves, so all the chunks get sent
        refresh=True if settings.TEST else False,  # update docs immediately when testing
    )
    errors = [
        error
        for error in errors
        if not (error.get("delete") and error["delete"]["status"] in [400, 404])
    ]
    if errors:
        raise BulkIndexError(f"{len(errors)} document(s) failed to index.", errors)


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

    # If we are in a test environment, refresh so that
    # documents will be updated/added directly in the index.
    if settings.TEST:
        doc_type._index.refresh()


@task
def delete_object(doc_type_name, obj_id):
    """Unindex an ORM object given an object id and document type name."""

    doc_type = next(cls for cls in get_doc_types() if cls.__name__ == doc_type_name)
    doc = doc_type()
    doc.meta.id = obj_id
    doc.to_action("delete")
