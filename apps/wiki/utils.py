import logging

from django.conf import settings

from statsd import statsd

from sumo.redis_utils import redis_client, RedisError
from wiki.models import Document


log = logging.getLogger('k.wiki')


def related_translated_documents(doc):
    if doc.parent:
        # Use a list because this version of
        # MySQL doesnt like LIMIT (the [0:5]) in a subquery.
        parent_related = doc.parent.related_documents
        parent_related = parent_related.order_by('-related_to__in_common')
        ids = list(parent_related.values_list('id', flat=True)[0:5])
        return Document.objects.filter(locale=doc.locale, parent__in=ids)
    return Document.objects.get_empty_query_set()


def find_related_documents(doc):
    """
    Returns a QuerySet of related_docuemnts or of the
    parent's related_documents in the case of translations
    """
    if doc.locale == settings.WIKI_DEFAULT_LANGUAGE:
        return doc.related_documents.order_by('-related_to__in_common')[0:5]

    # Not English, so may need related docs which are
    # stored on the English version.
    try:
        redis = redis_client('default')
    except RedisError as e:
        # Problem with Redis. Log and return the related docs.
        statsd.incr('redis.errror')
        log.error('Redis error: %s' % e)
        return related_translated_documents(doc)

    doc_key = 'translated_doc_id:%s' % doc.id
    related_ids = redis.lrange(doc_key, 0, -1)
    if related_ids == ['0']:
        return Document.objects.get_empty_query_set()
    if related_ids:
        return Document.objects.filter(id__in=related_ids)

    related = related_translated_documents(doc)
    if not related:
        # Add '0' to prevent recalulation on a known empty set.
        redis.lpush(doc_key, 0)
    else:
        for r in related:
            redis.lpush(doc_key, r.id)
    # Cache expires in 2 hours.
    redis.expire(doc_key, 60 * 60 * 2)
    return related
