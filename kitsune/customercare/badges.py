from datetime import date

from django.db.models.signals import post_save

from celery.task import task

from kitsune.kbadge.utils import get_or_create_badge
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

    maybe_award_badge.delay(AOA_BADGE, year, user)


@task
def maybe_award_badge(badge_info, year, user):
    """Award the specific badge to the user if they've earned it."""
    badge_slug = badge_info['slug'].format(year=year)
    badge = get_or_create_badge(
        slug=badge_slug,
        title=badge_info['title'].format(year=year),
        description=badge_info['description'].format(year=year))

    # If the user already has the badge, there is nothing else to do.
    if badge.is_awarded_to(user):
        return

    # Count the number of replies tweeted in the current year.
    qs = Reply.objects.filter(
        user=user,
        created__gte=date(year, 1, 1),
        created__lt=date(year + 1, 1, 1))

    # If the count is 50 or higher, award the badge.
    if qs.count() >= 50:
        badge.award_to(user)


def register_signals():
    post_save.connect(on_reply_save, sender=Reply)
