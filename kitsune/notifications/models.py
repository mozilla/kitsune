from datetime import datetime

from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

import actstream.registry
from actstream.models import Action

from kitsune.sumo.models import ModelBase


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
    from kitsune.notifications import tasks  # avoid circular import
    if not created:
        return
    tasks.add_notification_for_action.delay(instance.id)
