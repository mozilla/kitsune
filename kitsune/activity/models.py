from datetime import datetime

from django.contrib.auth.models import User
from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
from django.db import models

from kitsune.sumo.models import ModelBase


class Action(ModelBase):
    """Represents a unit of activity in a user's 'inbox.'"""
    users = models.ManyToManyField(User, related_name='action_inbox')
    creator = models.ForeignKey(User, null=True, blank=True,
                                related_name='actions')
    created = models.DateTimeField(default=datetime.now, db_index=True)
    data = models.CharField(max_length=400, blank=True)
    url = models.URLField(null=True, blank=True)
    content_type = models.ForeignKey(ContentType, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = generic.GenericForeignKey()
    formatter_cls = models.CharField(max_length=200,
                                     default='activity.ActionFormatter')

    class Meta(object):
        ordering = ['-created']

    @property
    def formatter(self):
        if not hasattr(self, 'fmt'):
            mod, _, cls = self.formatter_cls.rpartition('.')
            fmt_cls = getattr(__import__(mod, fromlist=[cls]), cls)
            self.fmt = fmt_cls(self)
        return self.fmt

    def __unicode__(self):
        return unicode(self.formatter)

    @property
    def title(self):
        return self.formatter.title

    @property
    def content(self):
        return self.formatter.content

    def get_absolute_url(self):
        return self.url


class ActionMixin(ModelBase):
    """Add a GenericRelation to a model."""
    actions = generic.GenericRelation(Action)

    class Meta(object):
        abstract = True
