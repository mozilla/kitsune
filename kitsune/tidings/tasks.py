from collections.abc import Sequence

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
def fire(
    event_cls_module_name,
    event_cls_name,
    instance_cls_module_name=None,
    instance_cls_name=None,
    instance_id=None,
    exclude_user_ids=None,
):
    """
    Celery task that is JSON-serializer friendly, and that fires the event specified by
    the "event_cls_*" arguments while excluding the users specified by "exclude_user_ids"
    if provided. The event will be constructed with the database model instance specified
    by the "instance_*" arguments if provided.
    """
    # Get the event class.
    event_cls = get_class(event_cls_module_name, event_cls_name)

    # Construct the event, either with or without an instance.
    if instance_cls_module_name and instance_cls_name and instance_id is not None:
        # Get the instance class, and then the instance itself from the database.
        instance_cls = get_class(instance_cls_module_name, instance_cls_name)
        instance = instance_cls.objects.get(id=instance_id)
        event = event_cls(instance)
    else:
        event = event_cls()

    # Get the excluded users, if any.
    if exclude_user_ids is None:
        exclude = None
    else:
        if not isinstance(exclude_user_ids, Sequence):
            exclude_user_ids = [exclude_user_ids]
        exclude = list(get_user_model().objects.filter(id__in=exclude_user_ids).all())

    event.fire(exclude=exclude)
