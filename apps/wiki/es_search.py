import elasticutils
import logging
import pyes

from search.es_utils import *


# TODO: Is this the right thing to log to?
log = logging.getLogger('k.wiki.es_search')


def setup_mapping(index):
    from wiki.models import Document

    # TODO: ES can infer types.  I don't know offhand if we can
    # provide some types and let it infer the rest.  If that's true,
    # then we can ditch all the defined types here except the strings
    # that need analysis.
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


def unindex_docs(docs):
    from wiki.models import Document

    es = elasticutils.get_es()
    index = get_index(Document)

    for doc_id in docs:
        # TODO wrap this in a try/except
        es.delete(index, doc_type=Document._meta.db_table, id=doc_id)


# TODO: This is seriously intensive and takes a _long_ time to run.
# Need to reduce the work here.  This should not get called often.
def reindex_documents():
    """Updates the mapping and indexes all documents."""
    from wiki.models import Document
    from django.conf import settings

    index = get_index(Document)

    log.info('reindex documents: %s %s', index, Document._meta.db_table)

    es = pyes.ES(settings.ES_HOSTS, timeout=10.0)

    log.info('setting up mapping....')
    setup_mapping(index)

    log.info('iterating through documents....')
    total = Document.objects.count()
    t = 0
    for d in Document.objects.all():
        t += 1
        if t % 1000 == 0:
            log.info('%s/%s...', t, total)

        index_doc(extract_document(d), bulk=True, es=es)

    es.flush_bulk(forced=True)
    log.info('done!')
    es.refresh()
