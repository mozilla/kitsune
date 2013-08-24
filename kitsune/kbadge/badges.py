from django.dispatch import receiver

from badger.signals import badge_was_awarded

from kitsune.kbadge.tasks import send_award_notification


@receiver(badge_was_awarded)
def notify_award_recipient(sender, **kwargs):
    """Notifies award recipient that he/she has an award!"""
    award = kwargs['award']

    # Kick off the task to send the email
    send_award_notification.delay(award)
