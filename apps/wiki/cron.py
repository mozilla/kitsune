import logging
import time

from django.db import connection, transaction

import cronjobs
from multidb.pinning import use_master
from statsd import statsd
import waffle

from wiki import tasks


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
            d2.current_revision_id IS NOT NULL
        GROUP BY
            t1.object_id,
            t2.object_id""")
    transaction.commit_unless_managed()


@cronjobs.register
def rebuild_kb():
    # If rebuild on demand switch is on, do nothing.
    if waffle.switch_is_active('wiki-rebuild-on-demand'):
        return

    tasks.rebuild_kb()


@cronjobs.register
@use_master
def migrate_helpfulvotes():
    """Transfer helpfulvotes from old to new version."""

    if not waffle.switch_is_active('migrate-helpfulvotes'):
        return

    start = time.time()





    transaction.enter_transaction_management()
    transaction.managed(True)
    try:
        start_id = 822800
        end_id = 825805
        cursor = connection.cursor()
        cursor.execute("""INSERT INTO `wiki_helpfulvote`
                    (revision_id, helpful, created,
                     creator_id, anonymous_id, user_agent)
SELECT COALESCE((SELECT id FROM `wiki_revision`
                              WHERE `document_id` = wiki_helpfulvoteold.document_id
                              AND `is_approved`=1 AND
                              (`reviewed` <= wiki_helpfulvoteold.created OR `reviewed` IS NULL)
                              ORDER BY CASE WHEN `reviewed`
                              IS NULL THEN 1 ELSE 0 END,
                              `wiki_revision`.`created` DESC LIMIT 1), 
        (SELECT id FROM `wiki_revision`
                                  WHERE `document_id` = wiki_helpfulvoteold.document_id
                                  AND (`reviewed` <= wiki_helpfulvoteold.created OR `reviewed` IS NULL)
                                  ORDER BY CASE WHEN `reviewed`
                                  IS NULL THEN 1 ELSE 0 END,
                                  `wiki_revision`.`created`  DESC LIMIT 1),
        (SELECT id FROM `wiki_revision`
                                  WHERE `document_id` = wiki_helpfulvoteold.document_id
                                  ORDER BY `created` ASC LIMIT 1)), helpful, created,
                        creator_id, anonymous_id, user_agent
                        FROM `wiki_helpfulvoteold` WHERE id >= %s AND id < %s""", [start_id, end_id])
        transaction.commit()
    except:
        transaction.rollback()
        raise

    transaction.leave_transaction_management()

    d = time.time() - start
    statsd.timing('wiki.migrate_helpfulvotes', int(round(d * 1000)))
