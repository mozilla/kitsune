from django.conf import settings
from django.db import models

from kitsune.sumo.utils import to_utf8mb3_str


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

    # TODO: Remove this in django 1.6, which comes with a smarter save().
    def update(self, **kw):
        """
        Shortcut for doing an UPDATE on this object.

        If _signal=False is in ``kw`` the post_save signal won't be sent.
        """
        signal = kw.pop("_signal", True)
        cls = self.__class__
        for k, v in list(kw.items()):
            setattr(self, k, v)
        if signal:
            # Detect any attribute changes during pre_save and add those to the
            # update kwargs.
            attrs = dict(self.__dict__)
            models.signals.pre_save.send(sender=cls, instance=self)
            for k, v in list(self.__dict__.items()):
                if attrs[k] != v:
                    kw[k] = v
                    setattr(self, k, v)
        cls.objects.filter(pk=self.pk).update(**kw)
        if signal:
            models.signals.post_save.send(sender=cls, instance=self, created=False)


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


class utf8mb3TextField(models.TextField):
    """
    TextField which strips 4-byte UTF-8 characters for storing in a utf8mb3 MySQL table.
    When html=True, replaces these characters with HTML numeric character references instead.
    """

    def __init__(self, *args, html=False, **kwargs):
        self.html = html
        super().__init__(*args, **kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        if self.html is not False:
            kwargs["html"] = self.html
        return name, path, args, kwargs

    def to_python(self, value):
        value = super().to_python(value)
        if value is not None:
            value = to_utf8mb3_str(value, self.html)
        return value


class utf8mb3CharField(models.CharField):
    """
    CharField which strips 4-byte UTF-8 characters for storing in a utf8mb3 MySQL table.
    """

    def to_python(self, value):
        value = super().to_python(value)
        if value is not None:
            value = to_utf8mb3_str(value)
        return value
