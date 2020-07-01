from datetime import datetime

from actstream.models import Action
from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

from kitsune.sumo.models import ModelBase


class Notification(ModelBase):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, db_index=True)
    action = models.ForeignKey(Action, on_delete=models.CASCADE)
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
    creator = models.ForeignKey(User, on_delete=models.CASCADE, db_index=True)
    created = models.DateTimeField(default=datetime.now)
    push_url = models.CharField(max_length=256)


@receiver(post_save, sender=Action, dispatch_uid="action_create_notifications")
def add_notification_for_action(sender, instance, created, **kwargs):
    """When an Action is created, notify every user following something in the Action."""
    if not created:
        return
    from kitsune.notifications import tasks  # avoid circular import

    tasks.add_notification_for_action.delay(instance.id)


@receiver(post_save, sender=Notification, dispatch_uid="send_notification")
def send_notification(sender, instance, created, **kwargs):
    if not created:
        return
    from kitsune.notifications import tasks  # avoid circular import

    tasks.send_notification.delay(instance.id)


class RealtimeRegistration(ModelBase):
    creator = models.ForeignKey(User, on_delete=models.CASCADE)
    created = models.DateTimeField(default=datetime.now)
    endpoint = models.CharField(max_length=256)

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    target = GenericForeignKey("content_type", "object_id")


@receiver(post_save, sender=Action, dispatch_uid="action_send_realtimes")
def send_realtimes_for_action(sender, instance, created, **kwargs):
    if not created:
        return
    from kitsune.notifications import tasks  # avoid circular import

    tasks.send_realtimes_for_action.delay(instance.id)
