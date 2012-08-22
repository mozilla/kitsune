import logging
import os
import time
import urllib2

from django.conf import settings
from django.db import connection, transaction

import cronjobs
from multidb.pinning import use_master
from statsd import statsd
import waffle

from search.tasks import index_task
from wiki import tasks
from wiki.models import Document


log = logging.getLogger('k.migratehelpful')


@cronjobs.register
def calculate_related_documents():
    """Calculates all related documents based on common tags."""

    cursor = connection.cursor()

    cursor.execute('DELETE FROM wiki_relateddocument')
    cursor.execute("""
        INSERT INTO
            wiki_relateddocument (document_id, related_id, in_common)
        SELECT
            t1.object_id,
            t2.object_id,
            COUNT(*) AS common_tags
        FROM
            wiki_document d1 JOIN
            taggit_taggeditem t1 JOIN
            taggit_taggeditem t2 JOIN
            wiki_document d2
        WHERE
            d1.id = t1.object_id AND
            t1.tag_id = t2.tag_id AND
            t1.object_id <> t2.object_id AND
            t1.content_type_id = (
                SELECT
                    id
                FROM
                    django_content_type
                WHERE
                    app_label = 'wiki' AND
                    model = 'document'
                ) AND
            t2.content_type_id = (
                SELECT
                    id
                FROM
                    django_content_type
                WHERE
                    app_label = 'wiki' AND
                    model = 'document'
                ) AND
            d2.id = t2.object_id AND
            d2.locale = d1.locale AND
            d2.category = d1.category AND
            d1.current_revision_id IS NOT NULL AND
            d2.current_revision_id IS NOT NULL AND
            d2.is_archived = 0
        GROUP BY
            t1.object_id,
            t2.object_id
        HAVING
            common_tags > 1""")
    transaction.commit_unless_managed()


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
    index_task.delay(Document, Document.get_indexable())
