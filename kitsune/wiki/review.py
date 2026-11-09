"""Applying a reviewer's decision to a revision."""

import logging
from datetime import datetime

from django.conf import settings
from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from kitsune.wiki.config import MAJOR_SIGNIFICANCE
from kitsune.wiki.content_managers import ManualContentManager, NotificationType
from kitsune.wiki.models import Revision, ScheduledRevision
from kitsune.wiki.strategies import (
    TranslationRequest,
    TranslationStrategy,
    TranslationStrategyFactory,
    TranslationTrigger,
)
from kitsune.wiki.tasks import render_document_cascade

log = logging.getLogger("k.wiki")

l10n_factory = TranslationStrategyFactory()


def execute_l10n_strategy(revision, trigger, user=None):
    """Execute l10n strategy for a given revision and trigger."""
    l10n_request = TranslationRequest(revision=revision, trigger=trigger, user=user)
    return l10n_factory.execute(l10n_request)


def apply_review(
    revision: Revision,
    reviewer: User,
    *,
    approve: bool,
    comment: str,
    significance: int | None,
    ready_for_localization: bool,
    needs_change: bool,
    needs_change_comment: str,
) -> None:
    doc = revision.document

    # Don't ask significance if this doc is a translation or if it has no
    # former approved versions:
    should_ask_significance = not doc.parent and doc.current_revision

    revision.is_approved = approve
    revision.reviewer = reviewer
    revision.reviewed = timezone.now()

    if should_ask_significance and significance:
        revision.significance = significance
    elif not should_ask_significance and not doc.parent:
        # This is a new document without approved revisions.
        # Significance is MAJOR.
        revision.significance = MAJOR_SIGNIFICANCE

    stale_schedules = Q(revision=revision)
    if approve:
        # An older revision can never become current once this one is approved.
        stale_schedules |= Q(document=doc, revision_id__lt=revision.id)
    # Atomic: Revision.save() stores the approval before it updates the document, which can fail.
    with transaction.atomic():
        ScheduledRevision.objects.filter(stale_schedules).delete()
        revision.save()

    # Only allow ready for l10n if the revision can actually be localized (not TYPO_SIGNIFICANCE)
    can_be_localized = TranslationStrategy.can_handle_revision(revision)
    is_ready_for_l10n = (
        ready_for_localization and doc.allows(reviewer, "mark_ready_for_l10n") and can_be_localized
    )
    match (revision.is_approved, is_ready_for_l10n):
        case (True, True):
            execute_l10n_strategy(revision, TranslationTrigger.REVIEW_REVISION, reviewer)
        case (True, False):
            ManualContentManager().fire_notifications(
                revision, [NotificationType.TRANSLATION_WORKFLOW]
            )
        case _:
            pass

    if (
        doc.locale == settings.WIKI_DEFAULT_LANGUAGE
        and doc.allows(reviewer, "edit_needs_change")
        and revision.is_approved
    ):
        doc.needs_change = needs_change

        if doc.needs_change:
            doc.needs_change_comment = needs_change_comment
        else:
            doc.needs_change_comment = ""

        doc.save()

    # Send review comment notification (separate from approval notifications).
    ManualContentManager().fire_notifications(
        revision, [NotificationType.REVIEW_WORKFLOW], comment=comment
    )

    render_document_cascade.delay(doc.id)


def schedule_revision(
    revision: Revision,
    reviewer: User,
    publish_at: datetime,
    *,
    comment: str,
    significance: int | None,
    ready_for_localization: bool,
    needs_change: bool,
    needs_change_comment: str,
) -> ScheduledRevision:
    """
    Store the reviewer's decision to approve the revision at publish_at, replacing any schedule
    of its document; the revision itself is left unreviewed.
    """
    schedule, _ = ScheduledRevision.objects.update_or_create(
        document=revision.document,
        defaults={
            "revision": revision,
            "publish_at": publish_at,
            "reviewer": reviewer,
            "comment": comment,
            "significance": significance,
            "is_ready_for_localization": ready_for_localization,
            "needs_change": needs_change,
            "needs_change_comment": needs_change_comment,
        },
    )
    return schedule


DROPPED_SCHEDULE = "Dropped the schedule of revision %s (document %s): %s"


def release_due_revisions(now: datetime | None = None) -> int:
    """
    Approve every revision whose publish time has come, as the reviewer who scheduled it.
    Schedules that no longer apply are dropped. Returns the number of revisions released.
    """
    now = now or timezone.now()
    due_ids = list(
        ScheduledRevision.objects.filter(publish_at__lte=now)
        .order_by("publish_at", "id")
        .values_list("id", flat=True)
    )

    released = 0
    for schedule_id in due_ids:
        # Read again: a reviewer may have rescheduled or reviewed it since the listing.
        schedule = (
            ScheduledRevision.objects.select_related("revision__document", "reviewer")
            .filter(pk=schedule_id, publish_at__lte=now)
            .first()
        )
        if schedule is None:
            continue
        revision, reviewer = schedule.revision, schedule.reviewer
        document = revision.document
        drop_reason: str | None = None
        if revision.reviewed is not None:
            drop_reason = "reviewed"
        elif document.current_revision_id and revision.id <= document.current_revision_id:
            drop_reason = "not newer than current"
        elif not reviewer.is_active:
            drop_reason = "reviewer inactive"
        elif not document.allows(reviewer, "review_revision"):
            drop_reason = "reviewer lost permission"
        if drop_reason:
            schedule.delete()
            log.info(DROPPED_SCHEDULE, revision.id, document.id, drop_reason)
            continue

        # The approval commits with the schedule's deletion, so a failure before then is retried.
        apply_review(
            revision,
            reviewer,
            approve=True,
            comment=schedule.comment,
            significance=schedule.significance,
            ready_for_localization=schedule.is_ready_for_localization,
            needs_change=schedule.needs_change,
            needs_change_comment=schedule.needs_change_comment,
        )
        released += 1
    return released
