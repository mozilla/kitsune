from datetime import datetime

from django.contrib.auth.models import User
from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
from django.db import models

from sumo.models import ModelBase


class Activity(ModelBase):
    """Represents a unit of activity in a user's 'inbox.'"""
    user = models.ForeignKey(User, related_name='activity_inbox')
    creator = models.ForeignKey(User, null=True, blank=True,
                                related_name='activity')
    created = models.DateTimeField(default=datetime.now, db_index=True)
    title = models.CharField(max_length=120)
    content = models.CharField(max_length=400, blank=True)
    url = models.URLField(null=True, blank=True)
    content_type = models.ForeignKey(ContentType, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = generic.GenericForeignKey()

    class Meta(object):
        ordering = ['-created']

    def __unicode__(self):
        return self.title

    def get_absolute_url(self):
        return self.url


class ActivityMixin(object):
    """Add a GenericRelation to a model."""
    activity = generic.GenericRelation(Activity)
