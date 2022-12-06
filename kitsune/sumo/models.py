from django.conf import settings
from django.db import models
from wagtail.models import Page


class ModelBase(models.Model):
    """Base class for SUMO models.

    * Adds objects_range class method.
    * Adds update method.
    """

    class Meta:
        abstract = True

    @classmethod
    def objects_range(cls, before=None, after=None):
        """
        Returns a QuerySet of rows updated before, after or between the supplied datetimes.

        The `updated_column_name` property must be defined on a model using this,
        as that will be used as the column to filter on.
        """
        column_name = getattr(cls, "updated_column_name", None)
        if not column_name:
            raise NotImplementedError

        queryset = cls._default_manager
        if before:
            queryset = queryset.filter(**{f"{column_name}__lt": before})
        if after:
            queryset = queryset.filter(**{f"{column_name}__gt": after})

        return queryset

    def update(self, **kw):
        """Shortcicuit to the update method."""
        self.__class__.objects.filter(pk=self.pk).update(**kw)


class WagtailBase(Page, ModelBase):
    ...

    class Meta:
        abstract = True


class LocaleField(models.CharField):
    """CharField with locale settings specific to SUMO defaults."""

    def __init__(
        self,
        max_length=7,
        default=settings.LANGUAGE_CODE,
        choices=settings.LANGUAGE_CHOICES,
        *args,
        **kwargs,
    ):
        return super(LocaleField, self).__init__(
            max_length=max_length, default=default, choices=choices, *args, **kwargs
        )
