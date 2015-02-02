from django.contrib.contenttypes.models import ContentType
from django.db.models import Q

import actstream.registry
from actstream.models import Action, Follow
from celery import task

from kitsune.notifications.models import Notification


@task()
def add_notification_for_action(action_id):
    action = Action.objects.get(id=action_id)

    # For each attribute of the action, check that the attribute is valid, and
    # build a query that finds all Follow objects that match it.
    actstream.registry.check(action.actor)
    query = Q(
        content_type=ContentType.objects.get_for_model(action.actor).pk,
        object_id=action.actor.pk)

    if action.target is not None:
        actstream.registry.check(action.target)
        query = query | Q(
            content_type=ContentType.objects.get_for_model(action.target).pk,
            object_id=action.target.pk,
            actor_only=False)

    if action.action_object is not None:
        actstream.registry.check(action.action_object)
        query = query | Q(
            content_type=ContentType.objects.get_for_model(action.action_object).pk,
            object_id=action.action_object.pk,
            actor_only=False)

    # execute the above query, iterate through the results, get every user
    # assocated with those Follow objects, and fire off a  notification to
    # every one of them. Use a set to only notify each user once.
    users_to_notify = set(f.user for f in Follow.objects.filter(query))
    notifications = [Notification(owner=u, action=action) for u in users_to_notify]
    Notification.objects.bulk_create(notifications)
