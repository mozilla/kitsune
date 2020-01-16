from datetime import datetime

from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.utils.translation import ugettext_lazy as _lazy

from kitsune.sumo.models import ModelBase


class FlaggedObjectManager(models.Manager):
    def pending(self):
        """Get all flagged objects that are pending moderation."""
        return self.filter(status=0)


class FlaggedObject(ModelBase):
    """A flag raised on an object."""

    REASONS = (
        ('spam', _lazy('Spam or other unrelated content')),
        ('language', _lazy('Inappropriate language/dialog')),
        ('bug_support', _lazy('Misplaced bug report or support request')),
        ('abuse', _lazy('Abusive content')),
        ('other', _lazy('Other (please specify)')),
    )

    STATUSES = (
        (0, _lazy('Pending')),
        (1, _lazy('Accepted and Fixed')),
        (2, _lazy('Rejected')),
    )

    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    status = models.IntegerField(default=0, db_index=True, choices=STATUSES)
    reason = models.CharField(max_length=64, choices=REASONS)
    notes = models.TextField(default='', blank=True)

    creator = models.ForeignKey(User, related_name='flags')
    created = models.DateTimeField(default=datetime.now, db_index=True)

    handled = models.DateTimeField(default=datetime.now, db_index=True)
    handled_by = models.ForeignKey(User, null=True)

    objects = FlaggedObjectManager()

    class Meta:
        unique_together = (('content_type', 'object_id', 'creator'),)
        ordering = ['created']
        permissions = (
            ('can_moderate', 'Can moderate flagged objects'),
        )
