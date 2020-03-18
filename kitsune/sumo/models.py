from django.conf import settings
from django.db import models


class ModelBase(models.Model):
    """Base class for SUMO models.

    * Adds update method.
    """

    class Meta:
        abstract = True

    # TODO: Remove this in django 1.6, which comes with a smarter save().
    def update(self, **kw):
        """
        Shortcut for doing an UPDATE on this object.

        If _signal=False is in ``kw`` the post_save signal won't be sent.
        """
        signal = kw.pop("_signal", True)
        cls = self.__class__
        for k, v in kw.items():
            setattr(self, k, v)
        if signal:
            # Detect any attribute changes during pre_save and add those to the
            # update kwargs.
            attrs = dict(self.__dict__)
            models.signals.pre_save.send(sender=cls, instance=self)
            for k, v in self.__dict__.items():
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
        **kwargs
    ):
        return super(LocaleField, self).__init__(
            max_length=max_length, default=default, choices=choices, *args, **kwargs
        )
