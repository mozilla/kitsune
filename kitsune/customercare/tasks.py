from datetime import date
from typing import Dict

from celery import task
from django.conf import settings
from django.contrib.auth.models import User
from sentry_sdk import capture_exception

from kitsune.customercare.models import Reply
from kitsune.kbadge.utils import get_or_create_badge


@task()
def maybe_award_badge(badge_template: Dict, year: int, user_id: int):
    """Award the specific badge to the user if they've earned it."""
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist as err:
        capture_exception(err)
        return

    badge = get_or_create_badge(badge_template, year)

    # If the user already has the badge, there is nothing else to do.
    if badge.is_awarded_to(user):
        return

    # Count the number of replies tweeted in the current year.
    qs = Reply.objects.filter(
        user=user, created__gte=date(year, 1, 1), created__lt=date(year + 1, 1, 1)
    )

    # If the count is 50 or higher, award the badge.
    if qs.count() >= settings.BADGE_LIMIT_ARMY_OF_AWESOME:
        badge.award_to(user)
        return True
