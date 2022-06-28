from celery import shared_task
from django.contrib.auth import get_user_model

from kitsune.tidings.models import Watch


@shared_task
def claim_watches(user_id):
    """
    Attach any anonymous watches having a user's email to that user.
    Call this from your user registration process if you like.
    """
    user = get_user_model().objects.get(id=user_id)
    Watch.objects.filter(email=user.email).update(email=None, user=user)
