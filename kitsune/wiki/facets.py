import hashlib

from django.conf import settings
from django.core.cache import cache
from django.db.models import Count

from elasticsearch.exceptions import TransportError
from statsd import statsd

from kitsune.products.models import Topic
from kitsune.wiki.models import Document, DocumentMappingType


def topics_for(product, parent=False):
    """Returns a list of topics that apply to passed in product.

    :arg product: a Product instance
    :arg parent: (optional) limit to topics with the given parent
    """
    statsd.incr('wiki.facets.topics_for.db')

    docs = Document.objects.filter(
        locale=settings.WIKI_DEFAULT_LANGUAGE,
        is_archived=False,
        current_revision__isnull=False,
        products=product,
        category__in=settings.IA_DEFAULT_CATEGORIES)

    qs = Topic.objects.filter(product=product)
    qs = (qs.filter(visible=True, document__in=docs)
            .annotate(num_docs=Count('document'))
            .distinct())

    if parent or parent is None:
        qs = qs.filter(parent=parent)

    return qs


def documents_for(locale, topics=None, products=None):
    """Returns a tuple of lists of articles that apply to topics and products.

    The first item in the tuple is the list of articles for the locale
    specified. The second item is the list of fallback articles in en-US
    that aren't localized to the specified locale. If the specified locale
    is en-US, the second item will be None.

    :arg locale: the locale
    :arg topics: (optional) a list of Topic instances
    :arg products: (optional) a list of Product instances

    The articles are returned as a list of dicts with the following keys:
        id
        document_title
        url
        document_parent_id
    """
    documents = _documents_for(locale, topics, products)

    # For locales that aren't en-US, get the en-US documents
    # to fill in for untranslated articles.
    if locale != settings.WIKI_DEFAULT_LANGUAGE:
        l10n_document_ids = [d['document_parent_id'] for d in documents if
                             'document_parent_id' in d]
        en_documents = _documents_for(
            locale=settings.WIKI_DEFAULT_LANGUAGE,
            products=products,
            topics=topics)
        fallback_documents = [d for d in en_documents if
                              d['id'] not in l10n_document_ids]
    else:
        fallback_documents = None

    return documents, fallback_documents


def _documents_for(locale, topics=None, products=None):
    """Returns a list of articles that apply to passed in topics and products.

    """
    # First try to get the results from the cache
    documents = cache.get(_documents_for_cache_key(
        locale, topics, products))
    if documents:
        statsd.incr('wiki.facets.documents_for.cache')
        return documents

    try:
        # Then try ES
        documents = _es_documents_for(locale, topics, products)
        cache.add(
            _documents_for_cache_key(locale, topics, products),
            documents)
        statsd.incr('wiki.facets.documents_for.es')
    except TransportError:
        # Finally, hit the database (through cache machine)
        # NOTE: The documents will be the same ones returned by ES
        # but they won't be in the correct sort (by votes in the last
        # 30 days). It is better to return them in the wrong order
        # than not to return them at all.
        documents = _db_documents_for(locale, topics, products)
        statsd.incr('wiki.facets.documents_for.db')

    return documents


def _es_documents_for(locale, topics=None, products=None):
    """ES implementation of documents_for."""
    s = (DocumentMappingType.search()
         .values_dict('id', 'document_title', 'url', 'document_parent_id',
                      'document_summary')
         .filter(document_locale=locale, document_is_archived=False,
                 document_category__in=settings.IA_DEFAULT_CATEGORIES))

    for topic in topics or []:
        s = s.filter(topic=topic.slug)
    for product in products or []:
        s = s.filter(product=product.slug)

    results = s.order_by('document_display_order', '-document_recent_helpful_votes')[:100]
    results = DocumentMappingType.reshape(results)
    return results


def _db_documents_for(locale, topics=None, products=None):
    """DB implementation of documents_for."""
    qs = Document.objects.filter(
        locale=locale,
        is_archived=False,
        current_revision__isnull=False,
        category__in=settings.IA_DEFAULT_CATEGORIES)
    for topic in topics or []:
        qs = qs.filter(topics=topic)
    for product in products or []:
        qs = qs.filter(products=product)

    # Convert the results to a dicts to look like the ES results.
    doc_dicts = []
    for d in qs.distinct():
        doc_dicts.append(dict(
            id=d.id,
            document_title=d.title,
            url=d.get_absolute_url(),
            document_parent_id=d.parent_id,
            document_summary=d.current_revision.summary))

    return doc_dicts


def _documents_for_cache_key(locale, topics, products):
    m = hashlib.md5()
    key = '{locale}:{topics}:{products}:new'.format(
        locale=locale,
        topics=','.join(sorted([t.slug for t in topics or []])),
        products=','.join(sorted([p.slug for p in products or []])))

    m.update(key)
    return 'documents_for:%s' % m.hexdigest()
