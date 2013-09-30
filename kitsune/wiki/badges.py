from django.conf import settings
from django.db.models.signals import post_save

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

    from kitsune.wiki.tasks import maybe_award_badge
    maybe_award_badge.delay(badge_template, year, creator)


def register_signals():
    post_save.connect(on_revision_save, sender=Revision)
