from celery import shared_task
from django.contrib.auth.models import User

from kitsune.users.models import UserProxy
from kitsune.customercare.zendesk import ZendeskClient


@shared_task
def update_zendesk_user(user_id: int) -> None:
    user = User.objects.get(pk=user_id)
    if user.profile.zendesk_id:
        zendesk = ZendeskClient()
        zendesk.update_user(user)


@shared_task
def update_zendesk_identity(user_key: str, email: str) -> None:
    user = UserProxy.get_user_from_key(user_key)
    zendesk_user_id = user and user.zendesk_id

    # fetch identity id
    if zendesk_user_id:
        zendesk = ZendeskClient()
        zendesk.update_primary_email(zendesk_user_id, email)
