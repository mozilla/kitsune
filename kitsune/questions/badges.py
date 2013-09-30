from django.db.models.signals import post_save

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

    * We award the Support Forum badge on 30 answers.
    """
    answer = instance
    year = answer.created.year
    creator = answer.creator

    # If this is a new answer (not an edit), then the creator
    # might qualify for the answers badge.
    if created:
        from kitsune.questions.tasks import maybe_award_badge
        maybe_award_badge.delay(
            QUESTIONS_BADGES['answer-badge'], year, creator)


def register_signals():
    post_save.connect(on_reply_save, sender=Answer)
