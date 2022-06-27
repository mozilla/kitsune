from celery import shared_task
from django.contrib.auth.models import User

from kitsune.customercare.zendesk import ZendeskClient


@shared_task
def update_zendesk_user(user_id: int) -> None:
    user = User.objects.get(pk=user_id)
    if user.profile.zendesk_id:
        zendesk = ZendeskClient()
        zendesk.update_user(user)


@shared_task
def update_zendesk_identity(user_id: int, email: str) -> None:
    user = User.objects.get(pk=user_id)
    zendesk_user_id = user.profile.zendesk_id

    # fetch identity id
    if zendesk_user_id:
        zendesk = ZendeskClient()
        zendesk.update_primary_email(zendesk_user_id, email)
