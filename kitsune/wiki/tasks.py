import logging
from datetime import date, datetime
from itertools import chain

import waffle
from celery import shared_task
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.core.mail import mail_admins
from django.db import transaction
from django.db.models import F, ObjectDoesNotExist, Q, Subquery
from django.db.models.functions import Coalesce
from django.urls import reverse as django_reverse
from django.utils.translation import gettext as _
from django.utils.translation import pgettext
from requests.exceptions import HTTPError
from sentry_sdk import capture_exception

from kitsune.community.utils import num_deleted_contributions
from kitsune.kbadge.utils import get_or_create_badge
from kitsune.products.models import Product
from kitsune.sumo import email_utils
from kitsune.sumo.decorators import skip_if_read_only_mode
from kitsune.sumo.urlresolvers import reverse
from kitsune.sumo.utils import BasicLoggerProtocol, chunked
from kitsune.wiki.badges import WIKI_BADGES
from kitsune.wiki.config import (
    HOW_TO_CATEGORY,
    REDIRECT_HTML,
    TEMPLATES_CATEGORY,
    TROUBLESHOOTING_CATEGORY,
)
from kitsune.wiki.models import (
    Document,
    Locale,
    Revision,
    SlugCollision,
    TitleCollision,
    resolves_to_document_view,
)
from kitsune.wiki.utils import generate_short_url

log = logging.getLogger("k.task")

shared_task_with_retry = shared_task(
    acks_late=True, autoretry_for=(Exception,), retry_backoff=2, retry_kwargs={"max_retries": 3}
)


@shared_task
def send_reviewed_notification(revision_id: int, message: str):
    """Send notification of review to the revision creator."""

    try:
        revision = Revision.objects.select_related("document").get(id=revision_id)
    except Revision.DoesNotExist as err:
        capture_exception(err)
        return
    else:
        document = revision.document

    if revision.reviewer == revision.creator:
        log.debug("Revision (id={}) reviewed by creator, skipping email".format(revision.id))
        return

    log.debug("Sending reviewed email for revision (id={})".format(revision.id))

    url = reverse("wiki.document_revisions", locale=document.locale, args=[document.slug])

    c = {
        "document_title": document.title,
        "approved": revision.is_approved,
        "reviewer": revision.reviewer,
        "message": message,
        "revisions_url": url,
        "host": Site.objects.get_current().domain,
    }

    # Skip if creator is a system account
    if hasattr(revision.creator, "profile") and revision.creator.profile.is_system_account:
        return

    if hasattr(revision.creator, "profile"):
        locale = revision.creator.profile.locale
    else:
        locale = settings.WIKI_DEFAULT_LANGUAGE

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

        return mail

    mail = _make_mail(locale, revision.creator)
    email_utils.send_messages([mail])


@shared_task
def send_contributor_notification(revision_id: int, message: str):
    """Send notification of review to the contributors of revisions."""

    try:
        revision = Revision.objects.select_related("document").get(id=revision_id)
    except Revision.DoesNotExist as err:
        capture_exception(err)
        return
    else:
        document = revision.document

    # Get all of the revisions created before this one but created
    # after the previously approved revision, if there is one.
    based_on = document.revisions.filter(
        created__lte=revision.created,
        created__gt=Coalesce(
            Subquery(
                document.revisions.filter(
                    is_approved=True,
                    created__lt=revision.created,
                )
                .order_by("-created")
                .values("created")[:1]
            ),
            datetime.min,
        ),
    )

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
            if user.profile.is_system_account:
                continue
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
def run_rebuild_kb(logger: BasicLoggerProtocol = log) -> None:
    """Try to run a KB rebuild, if we're allowed to."""
    if waffle.switch_is_active("wiki-rebuild-on-demand"):
        logger.info("Already rebuilding KB on-demand.")
        return

    if cache.get(settings.WIKI_REBUILD_TOKEN):
        logger.info("Rebuild task already scheduled.")
        return

    cache.set(settings.WIKI_REBUILD_TOKEN, True)

    rebuild_kb(logger=logger)


@shared_task
@skip_if_read_only_mode
def add_short_links(doc_ids):
    """Create short_url's for a list of docs."""
    base_url = "https://{}%s".format(Site.objects.get_current().domain)
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


@shared_task
@skip_if_read_only_mode
def generate_missing_share_links(logger: BasicLoggerProtocol = log) -> None:
    """Generate share links for documents without them."""
    document_ids = (
        Document.objects.filter(
            share_link="",
            is_template=False,
            is_archived=False,
            parent__isnull=True,
            current_revision__isnull=False,
            category__in=settings.IA_DEFAULT_CATEGORIES,
        )
        .exclude(html__startswith=REDIRECT_HTML)
        .values_list("id", flat=True)
    )
    document_ids = list(document_ids)
    logger.info(f"Generating share links for {len(document_ids)} documents")
    add_short_links.delay(document_ids)


@shared_task(rate_limit="3/h")
@skip_if_read_only_mode
def rebuild_kb(logger: BasicLoggerProtocol = log) -> None:
    """Re-render all documents in the KB in chunks."""
    cache.delete(settings.WIKI_REBUILD_TOKEN)

    d = (
        Document.objects.using("default")
        .filter(current_revision__isnull=False)
        .values_list("id", flat=True)
    )

    logger.info(f"Started rebuild of {d.count()} documents.")

    for chunk in chunked(d, 50):
        _rebuild_kb_chunk.delay(chunk)


@shared_task(rate_limit="5/m")
def _rebuild_kb_chunk(data: list[int]) -> None:
    """Re-render a chunk of documents.

    Note: Don't use host components when making redirects to wiki pages; those
    redirects won't be auto-pruned when they're 404s.

    """
    log.info(f"Rebuilding {len(data)} documents.")

    messages = []
    for pk in data:
        message = None
        try:
            document = Document.objects.get(pk=pk)

            # If we know a redirect link to be broken (i.e. if it looks like a
            # link to a document but the document isn't there), log an error:
            url = document.redirect_url()
            if url and resolves_to_document_view(url) and not document.redirect_document():
                log.warning(f"Invalid redirect document: {pk}")

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
        subject = "[{}] Exceptions raised in _rebuild_kb_chunk()".format(settings.PLATFORM_NAME)
        mail_admins(subject=subject, message="\n".join(messages))
    if not transaction.get_connection().in_atomic_block:
        transaction.commit()


@shared_task
@skip_if_read_only_mode
def maybe_award_badge(badge_template: dict, year: int, user_id: int) -> bool:
    """Award the specific badge to the user if they've earned it."""
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return False

    badge = get_or_create_badge(badge_template, year)

    # If the user already has the badge, there is nothing else to do.
    if badge.is_awarded_to(user):
        return False

    # Count the number of approved revisions in the appropriate locales
    # for the current year.
    qs = Revision.objects.filter(
        creator=user,
        is_approved=True,
        created__gte=date(year, 1, 1),
        created__lt=date(year + 1, 1, 1),
    )

    deleted_contributions_extra_kwargs: dict[str, str] = {}

    if badge_template["slug"] == WIKI_BADGES["kb-badge"]["slug"]:
        # kb-badge
        qs = qs.filter(document__locale=settings.WIKI_DEFAULT_LANGUAGE)
        deleted_contributions_extra_kwargs.update(locale=settings.WIKI_DEFAULT_LANGUAGE)
    else:
        # l10n-badge
        qs = qs.exclude(document__locale=settings.WIKI_DEFAULT_LANGUAGE)
        deleted_contributions_extra_kwargs.update(exclude_locale=settings.WIKI_DEFAULT_LANGUAGE)

    num_contributions = qs.count() + num_deleted_contributions(
        Revision,
        contributor=user,
        contribution_timestamp__gte=date(year, 1, 1),
        contribution_timestamp__lt=date(year + 1, 1, 1),
        metadata__is_approved=True,
        **deleted_contributions_extra_kwargs,
    )

    # If the count is 10 or higher, award the badge.
    if num_contributions >= settings.BADGE_LIMIT_L10N_KB:
        badge.award_to(user)
        return True

    return False


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


@shared_task_with_retry
@skip_if_read_only_mode
def translate(l10n_request_as_json: str) -> None:
    from kitsune.wiki.strategies import TranslationRequest, TranslationStrategyFactory

    l10n_request = TranslationRequest.from_json(l10n_request_as_json)
    if strategy := TranslationStrategyFactory().get_strategy(l10n_request.method):
        l10n_request.asynchronous = False
        strategy.translate(l10n_request)


@shared_task
@skip_if_read_only_mode
def process_stale_translations(limit=None) -> None:
    """Periodic task to process stale translations.

    Args:
        limit: Maximum number of stale translations to process
        (defaults to STALE_TRANSLATION_BATCH_SIZE)
    Returns:
        dict: Summary of processing results
    """
    from kitsune.wiki.services import StaleTranslationService

    service = StaleTranslationService()
    processed_candidates = service.process_stale(limit=limit)

    log.info(f"Processed {len(processed_candidates)} stale translations:")
    for parent, translated_doc, locale in processed_candidates:
        if translated_doc:
            log.info(translated_doc.get_absolute_url())


@shared_task
@skip_if_read_only_mode
def create_missing_translations(limit=None) -> None:
    """Periodic task to create missing translations for enabled locales.

    Args:
        limit: Maximum number of missing translations to process
        (defaults to STALE_TRANSLATION_BATCH_SIZE)
    """
    from kitsune.wiki.services import MissingTranslationService

    service = MissingTranslationService()
    processed_candidates = service.process_missing(limit=limit)

    log.info(f"Created {len(processed_candidates)} missing translations:")
    for english_doc, translation_doc, locale in processed_candidates:
        log.info(f"{english_doc.get_absolute_url()} -> {locale}")


@shared_task
@skip_if_read_only_mode
def publish_pending_translations() -> None:
    from kitsune.wiki.services import HybridTranslationService

    HybridTranslationService().publish_pending_translations(log=log)


@shared_task
@skip_if_read_only_mode
def send_weekly_ready_for_review_digest() -> None:
    """Sends out the weekly "Ready for review" digest email."""

    @email_utils.safe_translation
    def _make_digest_mail(locale, user, context):
        subject = _("[Reviews Pending: %s] SUMO needs your help!") % locale

        return email_utils.make_mail(
            subject=subject,
            text_template="wiki/email/ready_for_review_weekly_digest.ltxt",
            html_template="wiki/email/ready_for_review_weekly_digest.html",
            context_vars=context,
            from_email=settings.TIDINGS_FROM_ADDRESS,
            to_email=user.email,
        )

    # Get the list of revisions ready for review
    categories = (HOW_TO_CATEGORY, TROUBLESHOOTING_CATEGORY, TEMPLATES_CATEGORY)

    revs = Revision.objects.filter(
        reviewed=None, document__is_archived=False, document__category__in=categories
    )

    revs = revs.filter(
        Q(document__current_revision_id__lt=F("id")) | Q(document__current_revision_id=None)
    )

    locales = revs.values_list("document__locale", flat=True).distinct()
    products = Product.active.all()

    messages = []

    for loc in locales:
        doc_ids = revs.filter(document__locale=loc).values_list("document", flat=True).distinct()

        try:
            leaders = Locale.objects.get(locale=loc).leaders.all()
            reviewers = Locale.objects.get(locale=loc).reviewers.all()
            users = {user for user in chain(leaders, reviewers) if user.is_active}
        except ObjectDoesNotExist:
            # Locale does not exist, so skip to the next locale
            continue

        for user in users:
            docs_list = []
            docs = Document.objects.unrestricted(user, id__in=doc_ids)
            for product in products:
                product_docs = docs.filter(
                    Q(parent=None, products__in=[product]) | Q(parent__products__in=[product])
                )
                if product_docs:
                    docs_list.append(
                        {
                            "product": pgettext("DB: products.Product.title", product.title),
                            "docs": product_docs,
                        }
                    )

            product_docs = docs.filter(Q(parent=None, products=None) | Q(parent__products=None))

            if product_docs:
                docs_list.append({"product": _("Other products"), "docs": product_docs})

            messages.append(
                _make_digest_mail(
                    loc,
                    user,
                    {
                        "host": Site.objects.get_current().domain,
                        "locale": loc,
                        "recipient": user,
                        "docs_list": docs_list,
                        "products": products,
                    },
                )
            )

    email_utils.send_messages(messages)


@shared_task
@skip_if_read_only_mode
def fix_current_revisions(logger: BasicLoggerProtocol = log) -> None:
    """Fixes documents that have the current_revision set incorrectly."""
    # Reduce memory usage by only loading the columns we need.
    docs = Document.objects.all().values("id", "current_revision_id")

    for d in docs.iterator():
        revs = Revision.objects.filter(document_id=d["id"], is_approved=True)
        revs = revs.order_by(F("reviewed").desc(nulls_last=True)).values_list("id", flat=True)[:1]

        if len(revs):
            rev_id = revs[0]

            if d["current_revision_id"] != rev_id:
                doc = Document.objects.get(id=d["id"])
                doc.current_revision_id = rev_id
                doc.save()
                logger.info(doc.get_absolute_url())
