from django.db.models.signals import post_save

from kitsune.customercare.models import Reply


# Yo ******! These are year-agnostic badge templates which code uses
# to get-or-create the actual Badge instances. These strings should
# not be l10n-ized here--the badge title and description strings get
# l10n-ized elsewhere. Peace!
AOA_BADGE = {
    'slug': '{year}-army-of-awesome-badge',
    'title': '{year} Army of Awesome Badge',
    'description': 'This badge is awarded to contributors with 50 '
                   'Army of Awesome tweets during {year}.',
}


def on_reply_save(sender, instance, **kwargs):
    """Handle the reply save signal.

    * We award the Army of Awesome badge on 50 tweets.
    """
    reply = instance
    year = reply.created.year
    user = reply.user

    # If the user isn't logged in to SUMO, oh well....
    if not user:
        return

    from kitsune.customercare.tasks import maybe_award_badge
    maybe_award_badge.delay(AOA_BADGE, year, user)


def register_signals():
    post_save.connect(on_reply_save, sender=Reply)
