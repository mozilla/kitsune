import logging
import time

from django.conf import settings
from django.contrib.sites.models import Site
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.core.mail import send_mail, mail_admins, send_mass_mail
from django.db import transaction
from django.template import Context, loader

import celery.conf
from celery.task import task
from multidb.pinning import pin_this_thread, unpin_this_thread
from statsd import statsd
from tower import ugettext as _
import waffle

from sumo.urlresolvers import reverse
from sumo.utils import chunked
from wiki.models import (Document, points_to_document_view, SlugCollision,
                         TitleCollision, Revision)


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
        subject = _(u'Your revision has been reviewed: {title}')
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
    send_mass_mail(
        ((subject, content, settings.TIDINGS_FROM_ADDRESS, [who.email])
                    for who in [revision.creator, revision.reviewer]))


@task
def send_contributor_notification(based_on, revision, document, message):
    """Send notification of review to the contributors of revisions."""
    if revision.is_approved:
        subject = _(u'A revision you contributed to has '
                    'been approved: {title}')
    else:
        subject = _(u'A revision you contributed to has '
                    'been reviewed: {title}')
    subject = subject.format(title=document.title)
    t = loader.get_template('wiki/email/reviewed_contributors.ltxt')
    url = reverse('wiki.document_revisions', locale=document.locale,
                  args=[document.slug])
    content = t.render(Context({'document_title': document.title,
                                'approved': revision.is_approved,
                                'reviewer': revision.reviewer,
                                'message': message,
                                'url': url,
                                'host': Site.objects.get_current().domain}))

    # Send email to all contributors except the reviewer and the creator
    # of the approved revision.
    send_mail(subject, content, settings.TIDINGS_FROM_ADDRESS,
              [r.creator.email for r in based_on
               if r.creator not in [revision.creator, revision.reviewer]])


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


@task(rate_limit='10/m')
def _rebuild_kb_chunk(data):
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
            # link to a document but the document isn't there), log an error:
            url = document.redirect_url()
            if (url and points_to_document_view(url) and
                not document.redirect_document()):
                log.warn('Invalid redirect document: %d' % pk)

            html = Revision.objects.get(
                id=document.current_revision_id).content_parsed
            if document.html != html:
                # We are calling update here to so we only update the html
                # column instead of all of them. This bypasses post_save
                # signal handlers like the one that triggers reindexing.
                # See bug 797038 and bug 797352.
                Document.objects.filter(pk=pk).update(html=html)
        except Document.DoesNotExist:
            message = 'Missing document: %d' % pk
        except Revision.DoesNotExist:
            message = 'Missing revision for document: %d' % pk
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
