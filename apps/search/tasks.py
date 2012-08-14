import datetime
import logging
import sys

from celery.task import task
from statsd import statsd

from search.es_utils import index_chunk
from sumo.redis_utils import redis_client, RedisError


# This is present in memcached when reindexing is in progress and
# holds the number of outstanding index chunks. Once it hits 0,
# indexing is done.
OUTSTANDING_INDEX_CHUNKS = 'search:outstanding_index_chunks'

CHUNK_SIZE = 50000

log = logging.getLogger('k.task')


@task
def index_chunk_task(write_index, batch_id, chunk):
    """Index a chunk of things.

    :arg write_index: the name of the index to index to
    :arg batch_id: the name for the batch this chunk belongs to
    :arg chunk: a (class, id_list) of things to index
    """
    # Need to import Record here to prevent circular import
    from search.models import Record

    cls, id_list = chunk

    task_name = '%s %d -> %d' % (cls.get_model_name(), id_list[0], id_list[-1])

    rec = Record(
        starttime=datetime.datetime.now(),
        text=(u'Batch: %s Task: %s: Reindexing into %s' % (
                batch_id, task_name, write_index)))
    rec.save()

    try:
        index_chunk(cls, id_list, reraise=True)

    except Exception:
        rec.text = (u'%s: Errored out %s %s' % (
                rec.text, sys.exc_type, sys.exc_value))
        raise
    finally:
        rec.endtime = datetime.datetime.now()
        rec.save()

        try:
            client = redis_client('default')
            client.decr(OUTSTANDING_INDEX_CHUNKS, 1)
        except RedisError:
            # If Redis isn't running, then we just log that the task
            # was completed.
            log.info('Index task %s completed.', task_name)


# Note: If you reduce the length of RETRY_TIMES, it affects all tasks
# currently in the celery queue---they'll throw an IndexError.
RETRY_TIMES = (
    60,           # 1 minute
    5 * 60,       # 5 minutes
    10 * 60,      # 10 minutes
    30 * 60,      # 30 minutes
    60 * 60,      # 60 minutes
    )
MAX_RETRIES = len(RETRY_TIMES)


@task
def index_task(cls, ids, **kw):
    """Index documents specified by cls and ids"""
    statsd.incr('search.tasks.index_task.%s' % cls.get_model_name())
    try:
        for id in cls.uncached.filter(id__in=ids).values_list('id', flat=True):
            cls.index(cls.extract_document(id), refresh=True)
    except Exception as exc:
        retries = index_task.request.retries
        if retries >= MAX_RETRIES:
            raise

        index_task.retry(exc=exc, max_retries=MAX_RETRIES,
                         countdown=RETRY_TIMES[retries])


@task
def unindex_task(cls, ids, **kw):
    """Unindex documents specified by cls and ids"""
    statsd.incr('search.tasks.unindex_task.%s' % cls.get_model_name())
    try:
        for id in ids:
            cls.unindex(id)
    except Exception as exc:
        retries = unindex_task.request.retries
        if retries >= MAX_RETRIES:
            raise
        unindex_task.retry(exc=exc, max_retries=MAX_RETRIES,
                           countdown=RETRY_TIMES[retries])
