import logging
from datetime import datetime

from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

import actstream.registry
from actstream.models import Action
import requests
from requests.exceptions import RequestException

from kitsune.sumo.models import ModelBase
from kitsune.notifications.decorators import notification_handler


logger = logging.getLogger('k.notifications')


class Notification(ModelBase):
    owner = models.ForeignKey(User, db_index=True)
    action = models.ForeignKey(Action)
    read_at = models.DateTimeField(blank=True, null=True)

    @property
    def is_read(self):
        return self.read_at is not None

    @is_read.setter
    def is_read(self, newval):
        oldval = self.read_at is not None
        if not oldval and newval:
            self.read_at = datetime.now()
        elif oldval and not newval:
            self.read_at = None


class PushNotificationRegistration(ModelBase):
    creator = models.ForeignKey(User, db_index=True)
    created = models.DateTimeField(default=datetime.now)
    push_url = models.CharField(max_length=256)


actstream.registry.register(User)


@receiver(post_save, sender=Action, dispatch_uid='action_create_notifications')
def add_notification_for_action(sender, instance, created, **kwargs):
    """When an Action is created, notify every user following something in the Action."""
    if not created:
        return
    from kitsune.notifications import tasks  # avoid circular import
    tasks.add_notification_for_action.delay(instance.id)


@receiver(post_save, sender=Notification, dispatch_uid='send_notification')
def send_notification(sender, instance, created, **kwargs):
    if not created:
        return
    from kitsune.notifications import tasks  # avoid circular import
    tasks.send_notification.delay(instance.id)


@notification_handler
def simple_push(notification):
    """
    Send simple push notifications to users that have opted in to them.

    This will be called as a part of a celery task.
    """
    registrations = PushNotificationRegistration.objects.filter(creator=notification.owner)
    for reg in registrations:
        try:
            r = requests.put(reg.push_url, 'version={}'.format(notification.id))
            # If something does wrong, the SimplePush server will give back
            # json encoded error messages.
            if r.status_code != 200:
                logger.error('SimplePush error: %s %s', r.status_code, r.json())
        except RequestException as e:
            # This will go to Sentry.
            logger.error('SimplePush PUT failed: %s', e)
