import logging
import os
import urllib2

from django.conf import settings

import cronjobs
import waffle

from search.tasks import index_task
from wiki import tasks
from wiki.models import DocumentMappingType


log = logging.getLogger('k.migratehelpful')


@cronjobs.register
def rebuild_kb():
    # If rebuild on demand switch is on, do nothing.
    if waffle.switch_is_active('wiki-rebuild-on-demand'):
        return

    tasks.rebuild_kb()


@cronjobs.register
def reindex_kb():
    """Reindex wiki_document."""
    index_task.delay(DocumentMappingType, DocumentMappingType.get_indexable())
