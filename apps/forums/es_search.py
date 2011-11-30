import elasticutils
import logging
import pyes
import time

from search.es_utils import *


AGE_DIVISOR = 86400


# TODO: Is this the right thing to log to?
log = logging.getLogger('k.forums.es_search')


def setup_mapping(index):
    from forums.models import Post

    # TODO: ES can infer types.  I don't know offhand if we can
    # provide some types and let it infer the rest.  If that's true,
    # then we can ditch all the defined types here except the strings
    # that need analysis.
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
            'age': {TYPE: INTEGER},
            'replies': {TYPE: INTEGER}
            }
        }

    es = elasticutils.get_es()

    # TODO: If the mapping is there already and we do a put_mapping,
    # does that stomp on the existing mapping or raise an error?
    try:
        es.put_mapping(Post._meta.db_table, mapping, index)
    except pyes.exceptions.ElasticSearchException, e:
        log.error(e)


def extract_post(post):
    """Extracts indexable attributes from a Post"""
    d = {}
    d['id'] = post.id
    d['thread_id'] = post.thread.id
    d['forum_id'] = post.thread.forum.id
    d['title'] = post.thread.title
    d['is_sticky'] = post.thread.is_sticky
    d['is_locked'] = post.thread.is_locked
    d['author_id'] = post.author.id
    d['author_ord'] = post.author.username
    d['content'] = post.content
    d['created'] = post.thread.created
    if post.thread.last_post is not None:
        d['updated'] = post.thread.last_post.created
    else:
        d['updates'] = None

    # TODO: This isn't going to work right.  When we do incremental
    # updates, then we'll be comparing post with up-to-date ages with
    # post with stale ages.  We need to either change how this 'age'
    # thing works or update all the documents every 24 hours.  Keeping
    # it here for now.
    if post.updated is not None:
        updated_since_epoch = time.mktime(post.updated.timetuple())
        d['age'] = (time.time() - updated_since_epoch) / AGE_DIVISOR
    else:
        d['age'] = None

    d['replies'] = post.thread.replies
    return d


def index_post(post, bulk=False, force_insert=False, es=None):
    from forums.models import Post

    if es is None:
        es = elasticutils.get_es()

    index = get_index(Post)

    try:
        es.index(post, index, doc_type=Post._meta.db_table,
                 id=post['id'], bulk=bulk, force_insert=force_insert)
    except pyes.urllib3.TimeoutError:
        # If we have a timeout, try it again rather than die.  If we
        # have a second one, that will cause everything to die.
        es.index(post, index, doc_type=Post._meta.db_table,
                 id=post['id'], bulk=bulk, force_insert=force_insert)


# TODO: This is seriously intensive and takes a _long_ time to run.
# Need to reduce the work here.  This should not get called often.
def reindex_documents():
    """Updates the mapping and indexes all documents."""
    from forums.models import Post
    from django.conf import settings

    index = get_index(Post)

    log.info('reindex posts: %s %s', index, Post._meta.db_table)

    es = pyes.ES(settings.ES_HOSTS, timeout=10.0)

    log.info('setting up mapping....')
    setup_mapping(index)

    log.info('iterating through posts....')
    total = Post.objects.count()
    t = 0
    for p in Post.objects.all():
        t += 1
        if t % 1000 == 0:
            log.info('%s/%s...', t, total)

        index_post(extract_post(p), bulk=True, es=es)

    es.flush_bulk(forced=True)
    log.info('done!')
    es.refresh()
