from django.dispatch import receiver

from kitsune.kbadge.signals import badge_was_awarded
from kitsune.kbadge.tasks import send_award_notification


@receiver(badge_was_awarded)
def notify_award_recipient(sender, award, **kwargs):
    """Notifies award recipient that they have an award!"""
    send_award_notification.delay(award.id)
