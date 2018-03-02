import logging
from kitsune.forums.models import ThreadMappingType
from kitsune.search.tasks import index_task

import cronjobs

log = logging.getLogger('k.cron')


@cronjobs.register
def reindex_threads(seconds_ago=0):
    """Reindex forums_threads"""
    seconds_ago = int(seconds_ago)
    index_task.delay(ThreadMappingType,
                     ThreadMappingType.get_indexable(seconds_ago=seconds_ago))
