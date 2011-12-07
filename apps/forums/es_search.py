import elasticutils
import logging
import pyes
import time

from search.es_utils import (TYPE, INTEGER, STRING, ANALYZED, ANALYZER,
                             SNOWBALL, TERM_VECTOR, YES, STORE, BOOLEAN,
                             INDEX, WITH_POS_OFFSETS, DATE, get_index)


AGE_DIVISOR = 86400


log = logging.getLogger('k.forums.es_search')


def setup_mapping(index):
    from forums.models import Thread

    mapping = {
        'properties': {
            'id': {TYPE: INTEGER},
            'thread_id': {TYPE: INTEGER},
            'forum_id': {TYPE: INTEGER},
            'title': {TYPE: STRING, INDEX: ANALYZED, ANALYZER: SNOWBALL},
            'is_sticky': {TYPE: BOOLEAN},
            'is_locked': {TYPE: BOOLEAN},
            'author_id': {TYPE: INTEGER},
            'author_ord': {TYPE: STRING},
            'content': {TYPE: STRING, INDEX: ANALYZED, ANALYZER: SNOWBALL,
                        STORE: YES, TERM_VECTOR: WITH_POS_OFFSETS},
            'created': {TYPE: DATE},
            'updated': {TYPE: DATE},
            'replies': {TYPE: INTEGER}
            }
        }

    es = elasticutils.get_es()

    try:
        es.put_mapping(Thread._meta.db_table, mapping, index)
    except pyes.exceptions.ElasticSearchException, e:
        log.error(e)


def extract_thread(thread):
    """Extracts interesting thing from a Thread and its Posts"""
    d = {}
    d['id'] = thread.id
    d['forum_id'] = thread.forum.id
    d['title'] = thread.title
    d['is_sticky'] = thread.is_sticky
    d['is_locked'] = thread.is_locked
    d['created'] = thread.created

    if thread.last_post is not None:
        d['updated'] = thread.last_post.created
    else:
        d['updates'] = None

    d['replies'] = thread.replies

    author_ids = set()
    author_ords = set()
    content = []

    for post in thread.post_set.all():
        author_ids.add(post.author.id)
        author_ords.add(post.author.username)
        content.append(post.content)

    d['author_id'] = list(author_ids)
    d['author_ord'] = list(author_ords)
    d['content'] = '\n\n'.join(content)

    return d


def index_thread(thread, bulk=False, force_insert=False, es=None):
    from forums.models import Thread

    if es is None:
        es = elasticutils.get_es()

    index = get_index(Thread)

    try:
        es.index(thread, index, doc_type=Thread._meta.db_table,
                 id=thread['id'], bulk=bulk, force_insert=force_insert)
    except pyes.urllib3.TimeoutError:
        # If we have a timeout, try it again rather than die.  If we
        # have a second one, that will cause everything to die.
        es.index(thread, index, doc_type=Thread._meta.db_table,
                 id=thread['id'], bulk=bulk, force_insert=force_insert)


def unindex_threads(ids):
    from forums.models import Thread

    es = elasticutils.get_es()
    index = get_index(Thread)

    for thread_id in ids:
        try:
            es.delete(index, doc_type=Thread._meta.db_table, id=thread_id)
        except pyes.exception.NotFoundException:
            # If the document isn't in the index, then we ignore it.
            # TODO: Is that right?
            pass


def unindex_posts(ids):
    from forums.models import Post

    for post_id in ids:
        try:
            post = Post.objects.get(post_id)
            index_thread(extract_thread(post.thread))
        except Post.ObjectNotFound:
            pass


def reindex_documents(percent=100):
    """Updates the mapping and indexes all documents.

    Note: This only gets called from the command line.  Ergo we do
    some logging so the user knows what's going on.

    :arg percent: The percentage of questions to index.  Defaults to
        100--e.g. all of them.
    """
    from forums.models import Thread
    from django.conf import settings

    index = get_index(Thread)

    start_time = time.time()

    log.info('reindex threads: %s %s', index, Thread._meta.db_table)

    es = pyes.ES(settings.ES_HOSTS, timeout=10.0)

    log.info('setting up mapping....')
    setup_mapping(index)

    log.info('iterating through threads....')
    total = Thread.objects.count()
    to_index = int(total * (percent / 100.0))
    log.info('total threads: %s (to be indexed %s)', total, to_index)
    total = to_index

    t = 0
    for thread in Thread.objects.all():
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

        index_thread(extract_thread(thread), bulk=True, es=es)

    es.flush_bulk(forced=True)
    log.info('done!')
    es.refresh()
