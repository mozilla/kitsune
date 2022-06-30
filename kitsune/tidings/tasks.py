from importlib import import_module

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


@shared_task
def fire(
    app_name, event_cls_name, instance_cls_name=None, instance_id=None, exclude_user_ids=None
):
    """
    Celery task that is JSON-serializer friendly, and that fires the given app's event,
    which may be a plain event or an instance-based event, excluding the given user ids.
    """
    # Get the event class.
    event_cls = get_class(app_name, "events", event_cls_name)

    # Create the event, either instance-based or plain.
    if instance_cls_name and instance_id is not None:
        # Get the class of the instance and then the instance itself.
        instance_cls = get_class(app_name, "models", instance_cls_name)
        instance = instance_cls.objects.get(id=instance_id)
        event = event_cls(instance)
    else:
        event = event_cls()

    # Get the excluded users, if any.
    if exclude_user_ids:
        exclude = list(get_user_model().objects.filter(id__in=exclude_user_ids).all())
    else:
        exclude = None

    event.fire(exclude=exclude)


def get_class(app_name, module_name, class_name):
    """
    Convenience function for extracting a class from the given module name
    within the given kitsune app name.
    """
    module = import_module(f"kitsune.{app_name}.{module_name}")
    return getattr(module, class_name)
