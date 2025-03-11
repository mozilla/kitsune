import logging
from datetime import date
from typing import Dict, List

import waffle
from celery import shared_task
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.core.mail import mail_admins
from django.db import transaction
from django.urls import reverse as django_reverse
from django.utils.translation import gettext as _
from requests.exceptions import HTTPError
from sentry_sdk import capture_exception

from kitsune.kbadge.utils import get_or_create_badge
from kitsune.sumo import email_utils
from kitsune.sumo.decorators import skip_if_read_only_mode
from kitsune.sumo.urlresolvers import reverse
from kitsune.sumo.utils import chunked
from kitsune.wiki.badges import WIKI_BADGES
from kitsune.wiki.models import (
    Document,
    Revision,
    SlugCollision,
    TitleCollision,
    resolves_to_document_view,
)
from kitsune.wiki.utils import generate_short_url

log = logging.getLogger("k.task")


@shared_task
def send_reviewed_notification(revision_id: int, document_id: int, message: str):
    """Send notification of review to the revision creator."""

    try:
        revision = Revision.objects.get(id=revision_id)
        document = Document.objects.get(id=document_id)
    except (Revision.DoesNotExist, Document.DoesNotExist) as err:
        capture_exception(err)
        return

    if revision.reviewer == revision.creator:
        log.debug("Revision (id=%s) reviewed by creator, skipping email" % revision.id)
        return

    log.debug("Sending reviewed email for revision (id=%s)" % revision.id)

    url = reverse("wiki.document_revisions", locale=document.locale, args=[document.slug])

    c = {
        "document_title": document.title,
        "approved": revision.is_approved,
        "reviewer": revision.reviewer,
        "message": message,
        "revisions_url": url,
        "host": Site.objects.get_current().domain,
    }

    msgs = []

    @email_utils.safe_translation
    def _make_mail(locale, user):
        if revision.is_approved:
            subject = _("Your revision has been approved: {title}")
        else:
            subject = _("Your revision has been reviewed: {title}")
        subject = subject.format(title=document.title)

        mail = email_utils.make_mail(
            subject=subject,
            text_template="wiki/email/reviewed.ltxt",
            html_template="wiki/email/reviewed.html",
            context_vars=c,
            from_email=settings.TIDINGS_FROM_ADDRESS,
            to_email=user.email,
        )

        msgs.append(mail)

    for user in [revision.creator, revision.reviewer]:
        if hasattr(user, "profile"):
            locale = user.profile.locale
        else:
            locale = settings.WIKI_DEFAULT_LANGUAGE

        _make_mail(locale, user)

    email_utils.send_messages(msgs)


@shared_task
def send_contributor_notification(
    based_on_ids: List[int], revision_id: int, document_id: int, message: str
):
    """Send notification of review to the contributors of revisions."""

    try:
        revision = Revision.objects.get(id=revision_id)
        document = Document.objects.get(id=document_id)
    except (Revision.DoesNotExist, Document.DoesNotExist) as err:
        capture_exception(err)
        return

    based_on = Revision.objects.filter(id__in=based_on_ids)

    text_template = "wiki/email/reviewed_contributors.ltxt"
    html_template = "wiki/email/reviewed_contributors.html"
    url = reverse("wiki.document_revisions", locale=document.locale, args=[document.slug])
    c = {
        "document_title": document.title,
        "approved": revision.is_approved,
        "reviewer": revision.reviewer,
        "message": message,
        "revisions_url": url,
        "host": Site.objects.get_current().domain,
    }

    msgs = []

    @email_utils.safe_translation
    def _make_mail(locale, user):
        if revision.is_approved:
            subject = _("A revision you contributed to has been approved: {title}")
        else:
            subject = _("A revision you contributed to has been reviewed: {title}")
        subject = subject.format(title=document.title)

        mail = email_utils.make_mail(
            subject=subject,
            text_template=text_template,
            html_template=html_template,
            context_vars=c,
            from_email=settings.TIDINGS_FROM_ADDRESS,
            to_email=user.email,
        )

        msgs.append(mail)

    for r in based_on:
        # Send email to all contributors except the reviewer and the creator
        # of the approved revision.
        if r.creator in [revision.creator, revision.reviewer]:
            continue

        user = r.creator

        if hasattr(user, "profile"):
            locale = user.profile.locale
        else:
            locale = settings.WIKI_DEFAULT_LANGUAGE

        _make_mail(locale, user)

    email_utils.send_messages(msgs)


@skip_if_read_only_mode
def schedule_rebuild_kb():
    """Try to schedule a KB rebuild, if we're allowed to."""
    if not waffle.switch_is_active("wiki-rebuild-on-demand") or settings.CELERY_TASK_ALWAYS_EAGER:
        return

    if cache.get(settings.WIKI_REBUILD_TOKEN):
        log.debug("Rebuild task already scheduled.")
        return

    cache.set(settings.WIKI_REBUILD_TOKEN, True)

    rebuild_kb.delay()


@shared_task
@skip_if_read_only_mode
def add_short_links(doc_ids):
    """Create short_url's for a list of docs."""
    base_url = "https://{0}%s".format(Site.objects.get_current().domain)
    docs = Document.objects.filter(id__in=doc_ids)
    try:
        for doc in docs:
            # Use Django's reverse so the locale isn't included.
            # Since we're not including the locale in the URL, we
            # should always use the English slug. That ensures that
            # we'll find and redirect to the translation based on the
            # locale of the user using the short link.
            slug = doc.parent.slug if doc.parent else doc.slug
            endpoint = django_reverse("wiki.document", args=[slug])
            doc.update(share_link=generate_short_url(base_url % endpoint))
    except HTTPError:
        # The next run of the `generate_missing_share_links` cron job will
        # catch all documents that were unable to be processed.
        pass


@shared_task(rate_limit="3/h")
@skip_if_read_only_mode
def rebuild_kb():
    """Re-render all documents in the KB in chunks."""
    cache.delete(settings.WIKI_REBUILD_TOKEN)

    d = (
        Document.objects.using("default")
        .filter(current_revision__isnull=False)
        .values_list("id", flat=True)
    )

    for chunk in chunked(d, 50):
        _rebuild_kb_chunk.apply_async(args=[chunk])


@shared_task(rate_limit="5/m")
def _rebuild_kb_chunk(data):
    """Re-render a chunk of documents.

    Note: Don't use host components when making redirects to wiki pages; those
    redirects won't be auto-pruned when they're 404s.

    """
    log.info("Rebuilding %s documents." % len(data))

    messages = []
    for pk in data:
        message = None
        try:
            document = Document.objects.get(pk=pk)

            # If we know a redirect link to be broken (i.e. if it looks like a
            # link to a document but the document isn't there), log an error:
            url = document.redirect_url()
            if url and resolves_to_document_view(url) and not document.redirect_document():
                log.warn("Invalid redirect document: %d" % pk)

            html = document.parse_and_calculate_links()
            if document.html != html:
                # We are calling update here to so we only update the html
                # column instead of all of them. This bypasses post_save
                # signal handlers like the one that triggers reindexing.
                # See bug 797038 and bug 797352.
                Document.objects.filter(pk=pk).update(html=html)
        except Document.DoesNotExist:
            message = "Missing document: %d" % pk
        except Revision.DoesNotExist:
            message = "Missing revision for document: %d" % pk
        except ValidationError as e:
            message = "ValidationError for %d: %s" % (pk, e.messages[0])
        except SlugCollision:
            message = "SlugCollision: %d" % pk
        except TitleCollision:
            message = "TitleCollision: %d" % pk

        if message:
            log.debug(message)
            messages.append(message)

    if messages:
        subject = "[%s] Exceptions raised in _rebuild_kb_chunk()" % settings.PLATFORM_NAME
        mail_admins(subject=subject, message="\n".join(messages))
    if not transaction.get_connection().in_atomic_block:
        transaction.commit()


@shared_task
@skip_if_read_only_mode
def maybe_award_badge(badge_template: Dict, year: int, user_id: int):
    """Award the specific badge to the user if they've earned it."""
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return

    badge = get_or_create_badge(badge_template, year)

    # If the user already has the badge, there is nothing else to do.
    if badge.is_awarded_to(user):
        return

    # Count the number of approved revisions in the appropriate locales
    # for the current year.
    qs = Revision.objects.filter(
        creator=user,
        is_approved=True,
        created__gte=date(year, 1, 1),
        created__lt=date(year + 1, 1, 1),
    )
    if badge_template["slug"] == WIKI_BADGES["kb-badge"]["slug"]:
        # kb-badge
        qs = qs.filter(document__locale=settings.WIKI_DEFAULT_LANGUAGE)
    else:
        # l10n-badge
        qs = qs.exclude(document__locale=settings.WIKI_DEFAULT_LANGUAGE)

    # If the count is 10 or higher, award the badge.
    if qs.count() >= settings.BADGE_LIMIT_L10N_KB:
        badge.award_to(user)
        return True


@shared_task
@skip_if_read_only_mode
def render_document_cascade(base_doc_id):
    """Given a document, render it and all documents that may be affected."""

    # This walks along the graph of links between documents. If there is
    # a document A that includes another document B as a template, then
    # there is an edge from A to B in this graph. The goal here is to
    # process every node exactly once. This is robust to cycles and
    # diamonds in the graph, since it keeps track of what nodes have
    # been visited already.

    try:
        base_doc = Document.objects.get(id=base_doc_id)
    except Document.DoesNotExist as err:
        capture_exception(err)
        return
    todo = {base_doc}
    done = set()

    while todo:
        d = todo.pop()
        if d in done:
            # Don't process a node twice.
            continue
        d.html = d.parse_and_calculate_links()
        d.save()
        done.add(d)
        todo.update(
            link_to.linked_from
            for link_to in d.links_to().filter(kind__in=["template", "include"])
        )
