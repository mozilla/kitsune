from datetime import datetime

from django.contrib.auth.models import User
from django.db import models

import actstream.registry

from kitsune.sumo.models import ModelBase


class PushNotificationRegistration(ModelBase):

    creator = models.ForeignKey(User, db_index=True)
    created = models.DateTimeField(default=datetime.now)
    push_url = models.CharField(max_length=256)


actstream.registry.register(User)
