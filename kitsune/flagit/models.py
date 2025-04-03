from datetime import datetime

from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.translation import gettext_lazy as _lazy

from kitsune.sumo.models import ModelBase


class FlaggedObjectManager(models.Manager):
    def pending(self):
        """Get all flagged objects that are pending moderation."""
        return self.filter(status=FlaggedObject.FLAG_PENDING)


class FlaggedObject(ModelBase):
    """A flag raised on an object."""

    REASON_SPAM = "spam"
    REASON_LANGUAGE = "language"
    REASON_ABUSE = "abuse"
    REASON_CONTENT_MODERATION = "content_moderation"
    REASON_OTHER = "other"
    REASONS = (
        (REASON_SPAM, _lazy("Spam or other unrelated content")),
        (REASON_LANGUAGE, _lazy("Inappropriate language/dialog")),
        (REASON_ABUSE, _lazy("Abusive content")),
        (REASON_OTHER, _lazy("Other (please specify)")),
    )

    FLAG_PENDING = 0
    FLAG_ACCEPTED = 1
    FLAG_REJECTED = 2
    FLAG_DUPLICATE = 3
    STATUSES = (
        (FLAG_PENDING, _lazy("Pending")),
        (FLAG_ACCEPTED, _lazy("Accepted and Fixed")),
        (FLAG_REJECTED, _lazy("Rejected")),
    )

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey("content_type", "object_id")

    status = models.IntegerField(default=0, db_index=True, choices=STATUSES)
    reason = models.CharField(max_length=64, choices=REASONS, default="spam")
    notes = models.TextField(default="", blank=True)

    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name="flags")
    created = models.DateTimeField(default=datetime.now, db_index=True)

    handled = models.DateTimeField(default=datetime.now, db_index=True)
    handled_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True)

    assignee = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name="assigned_flags"
    )
    assigned_timestamp = models.DateTimeField(default=None, null=True)

    objects = FlaggedObjectManager()

    class Meta:
        unique_together = (("content_type", "object_id", "creator"),)
        ordering = ["created"]
        permissions = (("can_moderate", "Can moderate flagged objects"),)

    def save(self, *args, **kwargs):
        owner = None
        if hasattr(self.content_object, "creator"):
            owner = self.content_object.creator
        elif hasattr(self.content_object, "author"):
            owner = self.content_object.author

        if (
            int(self.status) == FlaggedObject.FLAG_ACCEPTED
            and owner
            and owner.profile.is_system_account
        ):
            self.content_object.delete()
            self.delete()
            return
        super().save(*args, **kwargs)
