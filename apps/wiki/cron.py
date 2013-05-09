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
def get_highcharts():
    """Fetch highcharts, v1.0.2."""
    localfilename = os.path.join(settings.MEDIA_ROOT, 'js', 'libs',
                                 'highstock.src.js')
    u = urllib2.urlopen('https://raw.github.com/highslide-software/'
                        'highcharts.com/7df98c2f1d7909edd212fea4519'
                        'd0bb87adac164/js/highstock.src.js')
    with open(localfilename, 'w') as f:
        f.write(u.read())


@cronjobs.register
def reindex_kb():
    """Reindex wiki_document."""
    index_task.delay(DocumentMappingType, DocumentMappingType.get_indexable())
