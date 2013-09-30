from datetime import date

from celery.task import task

from kitsune.customercare.models import Reply
from kitsune.kbadge.utils import get_or_create_badge


@task
def maybe_award_badge(badge_template, year, user):
    """Award the specific badge to the user if they've earned it."""
    badge = get_or_create_badge(badge_template, year)

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
        return True
