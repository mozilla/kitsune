import elasticutils
import logging
import pyes
import time

from search.es_utils import (TYPE, INTEGER, STRING, INDEX, ANALYZED, ANALYZER,
                             SNOWBALL, BOOLEAN, DATE, get_index)


log = logging.getLogger('k.wiki.es_search')


def setup_mapping(index):
    from wiki.models import Document

    mapping = {
        'properties': {
            'id': {TYPE: INTEGER},
            'title': {TYPE: STRING, INDEX: ANALYZED, ANALYZER: SNOWBALL},
            'locale': {TYPE: STRING},
            'current': {TYPE: INTEGER},
            'parent_id': {TYPE: INTEGER},
            'content':
                {TYPE: STRING, INDEX: ANALYZED, ANALYZER: SNOWBALL},
            'category': {TYPE: INTEGER},
            'slug': {TYPE: STRING},
            'is_archived': {TYPE: BOOLEAN},
            'summary': {TYPE: STRING},
            'keywords': {TYPE: STRING},
            'updated': {TYPE: DATE}
            }
        }

    es = elasticutils.get_es()

    # TODO: If the mapping is there already and we do a put_mapping,
    # does that stomp on the existing mapping or raise an error?
    try:
        es.put_mapping(Document._meta.db_table, mapping, index)
    except pyes.exceptions.ElasticSearchException, e:
        log.error(e)


def extract_document(doc):
    """Extracts indexable attributes from a Document"""
    d = {}
    d['id'] = doc.id
    d['title'] = doc.title
    d['locale'] = doc.locale
    d['parent_id'] = doc.parent.id if doc.parent else None
    d['content'] = doc.html
    d['category'] = doc.category
    d['slug'] = doc.slug
    d['is_archived'] = doc.is_archived
    if doc.current_revision:
        d['summary'] = doc.current_revision.summary
        d['keywords'] = doc.current_revision.keywords
        d['updated'] = doc.current_revision.created
        d['current'] = doc.current_revision.id
    else:
        d['summary'] = None
        d['keywords'] = None
        d['updated'] = None
        d['current'] = None
    return d


def index_doc(doc, bulk=False, force_insert=False, es=None):
    from wiki.models import Document

    if es is None:
        es = elasticutils.get_es()

    index = get_index(Document)

    try:
        es.index(doc, index, doc_type=Document._meta.db_table,
                 id=doc['id'], bulk=bulk, force_insert=force_insert)
    except pyes.urllib3.TimeoutError:
        # If we have a timeout, try it again rather than die.  If we
        # have a second one, that will cause everything to die.
        es.index(doc, index, doc_type=Document._meta.db_table,
                 id=doc['id'], bulk=bulk, force_insert=force_insert)


def unindex_documents(ids):
    from wiki.models import Document

    es = elasticutils.get_es()
    index = get_index(Document)

    for doc_id in ids:
        try:
            es.delete(index, doc_type=Document._meta.db_table, id=doc_id)
        except pyes.exceptions.NotFoundException:
            # If the document isn't in the index, then we ignore it.
            # TODO: Is that right?
            pass


def reindex_documents(percent):
    """Updates the mapping and indexes all documents.

    Note: This gets called from the commandline, so we do some logging
    so the user knows what's going on.

    :arg percent: The percentage of questions to index.  Defaults to
        100--e.g. all of them.
    """
    from wiki.models import Document
    from django.conf import settings

    index = get_index(Document)

    start_time = time.time()

    log.info('reindex documents: %s %s', index, Document._meta.db_table)

    es = pyes.ES(settings.ES_HOSTS, timeout=10.0)

    log.info('setting up mapping....')
    setup_mapping(index)

    log.info('iterating through documents....')
    total = Document.objects.count()
    to_index = int(total * (percent / 100.0))
    log.info('total documents: %s (to be indexed: %s)', total, to_index)
    total = to_index

    t = 0
    for d in Document.objects.all():
        t += 1
        if t % 1000 == 0:
            time_to_go = (total - t) * ((time.time() - start_time) / t)
            if time_to_go < 60:
                time_to_go = "%d secs" % time_to_go
            else:
                time_to_go = "%d min" % (time_to_go / 60)
            log.info('%s/%s...  (%s to go)', t, total, time_to_go)
            es.flush_bulk(forced=True)

        if t > total:
            break

        index_doc(extract_document(d), bulk=True, es=es)

    es.flush_bulk(forced=True)
    log.info('done!')
    es.refresh()
