from celery import shared_task

from kitsune.tidings.models import Watch


@shared_task
def claim_watches(user):
    """Attach any anonymous watches having a user's email to that user.

    Call this from your user registration process if you like.

    """
    Watch.objects.filter(email=user.email).update(email=None, user=user)
