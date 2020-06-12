import datetime
import logging
import sys
import traceback

from celery import task
from elasticutils.contrib.django import get_es
from multidb.pinning import pin_this_thread, unpin_this_thread

from kitsune.search.es_utils import (UnindexMeBro, get_analysis, index_chunk,
                                     write_index)
from kitsune.search.utils import from_class_path

# This is present in memcached when reindexing is in progress and
# holds the number of outstanding index chunks. Once it hits 0,
# indexing is done.
OUTSTANDING_INDEX_CHUNKS = "search:outstanding_index_chunks"

CHUNK_SIZE = 50000

log = logging.getLogger("k.task")


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


@task()
def index_chunk_task(write_index, batch_id, rec_id, chunk):
    """Index a chunk of things.

    :arg write_index: the name of the index to index to
    :arg batch_id: the name for the batch this chunk belongs to
    :arg rec_id: the id for the record for this task
    :arg chunk: a (class, id_list) of things to index
    """
    cls_path, id_list = chunk
    cls = from_class_path(cls_path)
    rec = None

    # Need to import Record here to prevent circular import
    from kitsune.search.models import Record

    try:
        # Pin to master db to avoid replication lag issues and stale data.
        pin_this_thread()

        # Update record data.
        rec = Record.objects.get(pk=rec_id)
        rec.start_time = datetime.datetime.now()
        rec.message = 'Reindexing into %s' % write_index
        rec.status = Record.STATUS_IN_PROGRESS
        rec.save()

        index_chunk(cls, id_list, reraise=True)
        rec.mark_success()

    except Exception:
        if rec is not None:
            rec.mark_fail('Errored out %s %s' % (sys.exc_info()[0], sys.exc_info()[1]))

        log.exception("Error while indexing a chunk")
        # Some exceptions aren't pickleable and we need this to throw
        # things that are pickleable.
        raise IndexingTaskError()

    finally:
        unpin_this_thread()


# Note: If you reduce the length of RETRY_TIMES, it affects all tasks
# currently in the celery queue---they'll throw an IndexError.
RETRY_TIMES = (
    60,  # 1 minute
    5 * 60,  # 5 minutes
    10 * 60,  # 10 minutes
    30 * 60,  # 30 minutes
    60 * 60,  # 60 minutes
)
MAX_RETRIES = len(RETRY_TIMES)


@task()
def index_task(cls_path, id_list, **kw):
    """Index documents specified by cls and ids"""
    cls = from_class_path(cls_path)
    try:
        # Pin to master db to avoid replication lag issues and stale
        # data.
        pin_this_thread()

        qs = cls.get_model().objects.filter(pk__in=id_list).values_list("pk", flat=True)
        for id_ in qs:
            try:
                cls.index(cls.extract_document(id_), id_=id_)
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

        index_task.retry(
            exc=exc, max_retries=MAX_RETRIES, countdown=RETRY_TIMES[retries]
        )
    finally:
        unpin_this_thread()


@task()
def unindex_task(cls_path, id_list, **kw):
    """Unindex documents specified by cls and ids"""
    cls = from_class_path(cls_path)
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

        unindex_task.retry(
            exc=exc, max_retries=MAX_RETRIES, countdown=RETRY_TIMES[retries]
        )
    finally:
        unpin_this_thread()


@task()
def update_synonyms_task():
    es = get_es()

    # Close the index, update the settings, then re-open it.
    # This will cause search to be unavailable for a few seconds.
    # This updates all of the analyzer settings, which is kind of overkill,
    # but will make sure everything stays consistent.
    index = write_index("default")
    analysis = get_analysis()

    # if anything goes wrong, it is very important to re-open the index.
    try:
        es.indices.close(index)
        es.indices.put_settings(index=index, body={"analysis": analysis,})
    finally:
        es.indices.open(index)
