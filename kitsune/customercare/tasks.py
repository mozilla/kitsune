from celery import task
from django.contrib.auth.models import User
from kitsune.customercare.zendesk import ZendeskClient


@task
def update_zendesk_user(user_id):
    user = User.objects.get(pk=user_id)
    if user.profile.zendesk_id:
        zendesk = ZendeskClient()
        zendesk.update_user(user)
