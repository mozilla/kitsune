from django.conf import settings
from django.db import transaction
from django.db.models.signals import post_save

from kitsune.wiki.models import Revision

# Yo ******! These are year-agnostic badge templates which code uses
# to get-or-create the actual Badge instances. These strings should
# not be l10n-ized here--the badge title and description strings get
# l10n-ized elsewhere. Peace!
WIKI_BADGES = {
    "kb-badge": {
        "slug": "{year}-kb-badge",
        "title": "{year} KB Badge",
        "description": "This badge is awarded to contributors with 10 "
        "approved English edits during {year}.",
    },
    "l10n-badge": {
        "slug": "{year}-l10n-badge",
        "title": "{year} L10n Badge",
        "description": "This badge is awarded to contributors with 10 "
        "approved translations edits during {year}.",
    },
    "reviewer-badge": {
        "slug": "{year}-reviewer-badge",
        "title": "{year} Reviewer Badge",
        "description": "This badge is awarded to KB reviewers with 25 "
        "or more reviews in {year}.",
    },
}


def on_revision_save(sender, instance, **kwargs):
    """Handle the revision save signal.

    * We award the KB badge on 10 approved en-US edits.
    * We award the L10n badge on 10 approved translation edits.
    * We award the Reviewer badge on 25 en-US reviews.
    """
    rev = instance
    created_year = rev.created.year
    creator_id = rev.creator_id
    reviewed_year = rev.reviewed.year if rev.reviewed else None
    reviewer_id = rev.reviewer_id

    from kitsune.wiki.tasks import maybe_award_badge

    # Queued on commit: the task counts approved revisions, and this one must be among them.
    # If the revision is reviewed (and in the default locale), maybe award the reviewer.
    if reviewer_id and reviewed_year and rev.document.locale == settings.WIKI_DEFAULT_LANGUAGE:
        transaction.on_commit(
            lambda: maybe_award_badge.delay(
                WIKI_BADGES["reviewer-badge"], reviewed_year, reviewer_id
            )
        )

    # If the revision is approved, maybe award the creator.
    if rev.is_approved:
        # The badge to be awarded depends on the locale.
        if rev.document.locale == settings.WIKI_DEFAULT_LANGUAGE:
            badge_template = WIKI_BADGES["kb-badge"]
        else:
            badge_template = WIKI_BADGES["l10n-badge"]

        transaction.on_commit(
            lambda: maybe_award_badge.delay(badge_template, created_year, creator_id)
        )


def register_signals():
    post_save.connect(on_revision_save, sender=Revision)
