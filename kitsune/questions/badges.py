from datetime import date

from django.db.models.signals import post_save

from celery.task import task

from kitsune.kbadge.utils import get_or_create_badge
from kitsune.questions.models import Answer


# Yo ******! These are year-agnostic badge templates which code uses
# to get-or-create the actual Badge instances. These strings should
# not be l10n-ized here--the badge title and description strings get
# l10n-ized elsewhere. Peace!
QUESTIONS_BADGES = {
    'answer-badge': {
        'slug': '{year}-support-forum-badge',
        'title': '{year} Support Forum Badge',
        'description': 'This badge is awarded to contributors with 20 '
                       'support forum replies during {year}.',
    },
}


def on_reply_save(sender, instance, created, **kwargs):
    """Handle the reply save signal.

    * We award the Support Forum badge on 20 answers.
    """
    answer = instance
    year = answer.created.year
    creator = answer.creator

    # If this is a new answer (not an edit), then the creator
    # might qualify for the answers badge.
    if created:
        maybe_award_badge.delay(
            QUESTIONS_BADGES['answer-badge'], year, creator)


@task
def maybe_award_badge(badge_template, year, user):
    """Award the specific badge to the user if they've earned it."""
    badge = get_or_create_badge(badge_template, year)

    # If the user already has the badge, there is nothing else to do.
    if badge.is_awarded_to(user):
        return

    # Count the number of replies tweeted in the current year.
    qs = Answer.objects.filter(
        creator=user,
        created__gte=date(year, 1, 1),
        created__lt=date(year + 1, 1, 1))

    # If the count is 20 or higher, award the badge.
    if qs.count() >= 20:
        badge.award_to(user)


def register_signals():
    post_save.connect(on_reply_save, sender=Answer)
