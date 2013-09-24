from django.conf import settings
from django.dispatch import receiver

from badger.signals import badge_was_awarded

from kitsune.kbadge.tasks import send_award_notification


@receiver(badge_was_awarded)
def notify_award_recipient(sender, award, **kwargs):
    """Notifies award recipient that he/she has an award!"""
    # -dev and -stage have STAGE = True which means they won't send
    # notification emails of newly awarded badges which would spam the
    # bejesus out of everyone.
    if not settings.STAGE:
        # Kick off the task to send the email
        send_award_notification.delay(award)
