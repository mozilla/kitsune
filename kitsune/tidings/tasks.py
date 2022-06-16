from celery import task

from kitsune.tidings.models import Watch


@task
def claim_watches(user):
    """Attach any anonymous watches having a user's email to that user.

    Call this from your user registration process if you like.

    """
    Watch.objects.filter(email=user.email).update(email=None, user=user)
