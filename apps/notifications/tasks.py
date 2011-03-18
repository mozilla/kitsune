from celery.decorators import task

from notifications.models import Watch


@task(rate_limit='1/m')
def claim_watches(user):
    """Attach any anonymous watches having a user's email to that user.

    Call this from your user registration process if you like.

    """
    Watch.objects.filter(email=user.email).update(email=None, user=user)
