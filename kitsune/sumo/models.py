from django.conf import settings
from django.db import models


class ModelBase(models.Model):
    """Base class for SUMO models."""

    class Meta:
        abstract = True


class LocaleField(models.CharField):
    """CharField with locale settings specific to SUMO defaults."""
    def __init__(self, max_length=7, default=settings.LANGUAGE_CODE,
                 choices=settings.LANGUAGE_CHOICES, *args, **kwargs):
        return super(LocaleField, self).__init__(
            max_length=max_length, default=default, choices=choices,
            *args, **kwargs)
