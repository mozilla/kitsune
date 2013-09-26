from datetime import date

from django.conf import settings
from django.db.models.signals import post_save

from celery.task import task

from kitsune.kbadge.utils import get_or_create_badge
from kitsune.wiki.models import Revision


# Yo ******! These are year-agnostic badge templates which code uses
# to get-or-create the actual Badge instances. These strings should
# not be l10n-ized here--the badge title and description strings get
# l10n-ized elsewhere. Peace!
WIKI_BADGES = {
    'kb-badge': {
        'slug': '{year}-kb-badge',
        'title': '{year} KB Badge',
        'description': 'This badge is awarded to contributors with 10 '
                       'approved English edits during {year}.',
    },
    'l10n-badge': {
        'slug': '{year}-l10n-badge',
        'title': '{year} L10n Badge',
        'description': 'This badge is awarded to contributors with 10 '
                       'approved translations edits during {year}.',
    },
}


def on_revision_save(sender, instance, **kwargs):
    """Handle the revision save signal.

    * We award the KB badge on 10 approved en-US edits.
    * We award the L10n badge on 10 approved translation edits.
    """
    rev = instance
    year = rev.created.year
    creator = rev.creator

    # We only care about approved revisions.
    if not rev.is_approved:
        return

    # The badge to be awarded depends on the locale.
    if rev.document.locale == settings.WIKI_DEFAULT_LANGUAGE:
        badge_template = WIKI_BADGES['kb-badge']
    else:
        badge_template = WIKI_BADGES['l10n-badge']

    maybe_award_badge.delay(badge_template, year, creator)


@task
def maybe_award_badge(badge_template, year, user):
    """Award the specific badge to the user if they've earned it."""
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
        created__lt=date(year + 1, 1, 1))
    if badge_template['slug'] == WIKI_BADGES['kb-badge']['slug']:
        # kb-badge
        qs = qs.filter(document__locale=settings.WIKI_DEFAULT_LANGUAGE)
    else:
        # l10n-badge
        qs = qs.exclude(document__locale=settings.WIKI_DEFAULT_LANGUAGE)

    # If the count is 10 or higher, award the badge.
    if qs.count() >= 10:
        badge.award_to(user)
        return True


def register_signals():
    post_save.connect(on_revision_save, sender=Revision)
