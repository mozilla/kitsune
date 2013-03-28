import datetime
import logging
import sys
import traceback

from celery.task import task
from multidb.pinning import pin_this_thread, unpin_this_thread
from statsd import statsd

from search.es_utils import index_chunk, UnindexMeBro
from sumo.redis_utils import redis_client, RedisError


# This is present in memcached when reindexing is in progress and
# holds the number of outstanding index chunks. Once it hits 0,
# indexing is done.
OUTSTANDING_INDEX_CHUNKS = 'search:outstanding_index_chunks'

CHUNK_SIZE = 50000

log = logging.getLogger('k.task')


class IndexingTaskError(Exception):
    """Exception that captures current exception information

    Some exceptions aren't pickleable. This uses traceback module to
    format the exception that's currently being thrown and tosses it
    in the message of IndexingTaskError at the time the
    IndexingTaskError is created.

    So you can do this::

        try:
            # some code that throws an error
        except Exception as exc:
            raise IndexingTaskError()

    The message will have the message and traceback from the original
    exception thrown.

    Yes, this is goofy.

    """
    def __init__(self):
        super(IndexingTaskError, self).__init__(traceback.format_exc())


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

    task_name = '{0} {1} -> {2}'.format(
        cls.get_model_name(), id_list[0], id_list[-1])

    rec = Record(
        starttime=datetime.datetime.now(),
        text=(u'Batch: %s Task: %s: Reindexing into %s' % (
                batch_id, task_name, write_index)))
    rec.save()

    try:
        # Pin to master db to avoid replication lag issues and stale
        # data.
        pin_this_thread()

        index_chunk(cls, id_list, reraise=True)

    except Exception:
        rec.text = (u'%s: Errored out %s %s' % (
                rec.text, sys.exc_type, sys.exc_value))
        # Some exceptions aren't pickleable and we need this to throw
        # things that are pickleable.
        raise IndexingTaskError()

    finally:
        unpin_this_thread()
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
def index_task(cls, id_list, **kw):
    """Index documents specified by cls and ids"""
    statsd.incr('search.tasks.index_task.%s' % cls.get_model_name())
    try:
        # Pin to master db to avoid replication lag issues and stale
        # data.
        pin_this_thread()

        qs = cls.uncached.filter(id__in=id_list).values_list('id', flat=True)
        for id_ in qs:
            try:
                cls.index(cls.extract_document(id_))
            except UnindexMeBro:
                # If extract_document throws this, then we need to
                # remove this item from the index.
                cls.unindex(id_)

    except Exception as exc:
        retries = index_task.request.retries
        if retries >= MAX_RETRIES:
            # Some exceptions aren't pickleable and we need this to
            # throw things that are pickleable.
            raise IndexingTaskError()

        statsd.incr('search.tasks.index_task.retry', 1)
        statsd.incr('search.tasks.index_task.retry%d' % RETRY_TIMES[retries],
                    1)

        index_task.retry(exc=exc, max_retries=MAX_RETRIES,
                         countdown=RETRY_TIMES[retries])
    finally:
        unpin_this_thread()


@task
def unindex_task(cls, id_list, **kw):
    """Unindex documents specified by cls and ids"""
    statsd.incr('search.tasks.unindex_task.%s' % cls.get_model_name())
    try:
        # Pin to master db to avoid replication lag issues and stale
        # data.
        pin_this_thread()
        for id_ in id_list:
            cls.unindex(id_)
    except Exception as exc:
        retries = unindex_task.request.retries
        if retries >= MAX_RETRIES:
            # Some exceptions aren't pickleable and we need this to
            # throw things that are pickleable.
            raise IndexingTaskError()

        statsd.incr('search.tasks.unindex_task.retry', 1)
        statsd.incr('search.tasks.unindex_task.retry%d' % RETRY_TIMES[retries],
                    1)

        unindex_task.retry(exc=exc, max_retries=MAX_RETRIES,
                           countdown=RETRY_TIMES[retries])
    finally:
        unpin_this_thread()
