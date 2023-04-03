from django.db import models

from kitsune.sumo import form_fields


class ImagePlusField(models.ImageField):
    """
    Same as models.ImageField but with support for SVG images as well.
    """

    def formfield(self, **kwargs):
        return super().formfield(
            **{
                "form_class": form_fields.ImagePlusField,
                **kwargs,
            }
        )
