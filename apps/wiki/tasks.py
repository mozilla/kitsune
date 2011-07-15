import logging
import time

from django.conf import settings
from django.contrib.sites.models import Site
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.core.mail import send_mail, mail_admins
from django.db import transaction
from django.template import Context, loader

import celery.conf
from celery.decorators import task
from multidb.pinning import pin_this_thread, unpin_this_thread
from statsd import statsd
from tower import ugettext as _
import waffle

from sumo.urlresolvers import reverse
from sumo.utils import chunked
from wiki.models import (Document, points_to_document_view, SlugCollision,
                         TitleCollision)


log = logging.getLogger('k.task')


@task
def send_reviewed_notification(revision, document, message):
    """Send notification of review to the revision creator."""
    if revision.reviewer == revision.creator:
        log.debug('Revision (id=%s) reviewed by creator, skipping email' % \
                  revision.id)
        return

    log.debug('Sending reviewed email for revision (id=%s)' % revision.id)
    if revision.is_approved:
        subject = _(u'Your revision has been approved: {title}')
    else:
        subject = _(u'Your revision has been rejected: {title}')
    subject = subject.format(title=document.title)
    t = loader.get_template('wiki/email/reviewed.ltxt')
    url = reverse('wiki.document_revisions', locale=document.locale,
                  args=[document.slug])
    content = t.render(Context({'document_title': document.title,
                                'approved': revision.is_approved,
                                'reviewer': revision.reviewer,
                                'message': message,
                                'url': url,
                                'host': Site.objects.get_current().domain}))
    send_mail(subject, content, settings.TIDINGS_FROM_ADDRESS,
              [revision.creator.email])


def schedule_rebuild_kb():
    """Try to schedule a KB rebuild, if we're allowed to."""
    if (not waffle.switch_is_active('wiki-rebuild-on-demand') or
        celery.conf.ALWAYS_EAGER):
        return

    if cache.get(settings.WIKI_REBUILD_TOKEN):
        log.debug('Rebuild task already scheduled.')
        return

    cache.set(settings.WIKI_REBUILD_TOKEN, True)

    rebuild_kb.delay()


@task(rate_limit='3/h')
def rebuild_kb():
    """Re-render all documents in the KB in chunks."""
    cache.delete(settings.WIKI_REBUILD_TOKEN)

    d = (Document.objects.using('default')
         .filter(current_revision__isnull=False).values_list('id', flat=True))

    for chunk in chunked(d, 100):
        _rebuild_kb_chunk.apply_async(args=[chunk])


@task(rate_limit='20/m')
def _rebuild_kb_chunk(data, **kwargs):
    """Re-render a chunk of documents.

    Note: Don't use host components when making redirects to wiki pages; those
    redirects won't be auto-pruned when they're 404s.

    """
    log.info('Rebuilding %s documents.' % len(data))

    pin_this_thread()  # Stick to master.

    messages = []
    start = time.time()
    for pk in data:
        message = None
        try:
            document = Document.objects.get(pk=pk)

            # If we know a redirect link to be broken (i.e. if it looks like a
            # link to a document but the document isn't there), delete it:
            url = document.redirect_url()
            if (url and points_to_document_view(url) and
                not document.redirect_document()):
                document.delete()
            else:
                document.html = document.current_revision.content_parsed
                document.save()
        except Document.DoesNotExist:
            message = 'Missing document: %d' % pk
        except ValidationError as e:
            message = 'ValidationError for %d: %s' % (pk, e.messages[0])
        except SlugCollision:
            message = 'SlugCollision: %d' % pk
        except TitleCollision:
            message = 'TitleCollision: %d' % pk

        if message:
            log.debug(message)
            messages.append(message)
    d = time.time() - start
    statsd.timing('wiki.rebuild_chunk', int(round(d * 1000)))

    if messages:
        subject = ('[%s] Exceptions raised in _rebuild_kb_chunk()' %
                   settings.PLATFORM_NAME)
        mail_admins(subject=subject, message='\n'.join(messages))
    transaction.commit_unless_managed()

    unpin_this_thread()  # Not all tasks need to do use the master.


@task(rate_limit='1/h')
def migrate_helpfulvotes(start_id, end_id):
    """Transfer helpfulvotes from old to new version."""

    if not waffle.switch_is_active('migrate-helpfulvotes'):
        return  # raise? Celery can email us the failed ID range then

    start = time.time()

    pin_this_thread()  # Pin to master

    transaction.enter_transaction_management()
    transaction.managed(True)
    try:
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

    unpin_this_thread()

    d = time.time() - start
    statsd.timing('wiki.migrate_helpfulvotes', int(round(d * 1000)))
