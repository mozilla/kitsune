from celery import shared_task
from django.contrib.auth import get_user_model

from kitsune.tidings.models import Watch
from kitsune.tidings.utils import get_class


@shared_task
def claim_watches(user_id):
    """
    Attach any anonymous watches having a user's email to that user.
    Call this from your user registration process if you like.
    """
    user = get_user_model().objects.get(id=user_id)
    Watch.objects.filter(email=user.email).update(email=None, user=user)


@shared_task
def send_emails(event_info, exclude_user_ids=None):
    """
    Celery task that is JSON-serializer friendly, and that fires the event specified by
    the "event_cls_*" arguments while excluding the users specified by "exclude_user_ids"
    if provided. The event will be constructed with the database model instance specified
    by the "instance_*" arguments if provided.
    """
    event_cls_info = event_info["event"]
    instance_info = event_info.get("instance")

    # Get the event class.
    event_cls = get_class(event_cls_info["module"], event_cls_info["class"])

    # Construct the event, either with or without an instance.
    if instance_info:
        # Get the instance class, and then the instance itself from the database.
        instance_cls = get_class(instance_info["module"], instance_info["class"])
        instance = instance_cls.objects.get(id=instance_info["id"])
        event = event_cls(instance)
    else:
        event = event_cls()

    # Get the excluded users, if any.
    if exclude_user_ids:
        exclude = None
    else:
        exclude = list(get_user_model().objects.filter(id__in=exclude_user_ids).all())

    event.send_emails(exclude=exclude)
