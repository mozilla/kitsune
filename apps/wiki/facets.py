import hashlib

from django.core.cache import cache

from statsd import statsd

from products.models import Product
from search.es_utils import ESMaxRetryError, ESTimeoutError, ESException
from topics.models import Topic
from wiki.models import Document


def products_for(topics):
    """Returns a list of products that apply to passed in topics.

    :arg topics: a list of Topic instances
    """
    statsd.incr('wiki.facets.products_for.db')

    docs = Document.objects
    for topic in topics:
        docs = docs.filter(topics=topic)
    return Product.objects.filter(document__in=docs).distinct()


def topics_for(products):
    """Returns a list of topics that apply to passed in products.

    :arg products: a list of Product instances
    """
    statsd.incr('wiki.facets.topics_for.db')

    docs = Document.objects
    for product in products:
        docs = docs.filter(products=product)
    return Topic.objects.filter(document__in=docs).distinct()


def documents_for(locale, topics, products=None):
    """Returns a list of articles that apply to passed in topics and products.

    :arg locale: the locale
    :arg topics: a list of Topic instances
    :arg products: (optional) a list of Product instances

    The articles are returned as a list of dicts with the following keys:
        id
        document_title
        url
    """
    # First try to get the results from the cache
    documents = cache.get(_documents_for_cache_key(locale, topics, products))
    if documents:
        statsd.incr('wiki.facets.documents_for.cache')
        return documents

    try:
        # Then try ES
        documents = _es_documents_for(locale, topics, products)
        cache.add(
            _documents_for_cache_key(locale, topics, products), documents)
        statsd.incr('wiki.facets.documents_for.es')
    except (ESMaxRetryError, ESTimeoutError, ESException):
        # Finally, hit the database (through cache machine)
        # NOTE: The documents will be the same ones returned by ES
        # but they won't be in the correct sort (by votes in the last
        # 30 days). It is better to return them in the wrong order
        # than not to return them at all.
        documents = _db_documents_for(locale, topics, products)
        statsd.incr('wiki.facets.documents_for.db')

    return documents


def _es_documents_for(locale, topics, products):
    """ES implementation of documents_for."""
    s = Document.search().values_dict(
        'id', 'document_title', 'url').filter(document_locale=locale)
    for topic in topics:
        s = s.filter(document_topic=topic.slug)
    for product in products or []:
        s = s.filter(document_product=product.slug)

    return list(s.order_by('-document_recent_helpful_votes')[:100])


def _db_documents_for(locale, topics, products=None):
    """DB implementation of topics_for."""
    qs = Document.objects.filter(locale=locale)
    for topic in topics:
        qs = qs.filter(topics=topic)
    for product in products or []:
        qs = qs.filter(products=product)

    # Convert the results to a dicts to look like the ES results.
    doc_dicts = []
    for d in qs.distinct():
        doc_dicts.append(dict(
            id=d.id, document_title=d.title, url=d.get_absolute_url()))
    return doc_dicts


def _documents_for_cache_key(locale, topics, products):
    m = hashlib.md5()
    m.update('{locale}:{topics}:{products}'.format(
        locale=locale,
        topics=','.join(sorted([t.slug for t in topics])),
        products=','.join(sorted([p.slug for p in products or []]))))
    return 'documents_for:%s' % m.hexdigest()
