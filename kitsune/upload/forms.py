from django import forms
from django.conf import settings
from django.core.validators import FileExtensionValidator
from django.utils.translation import ugettext_lazy as _lazy

MSG_IMAGE_REQUIRED = _lazy("You have not selected an image to upload.")
MSG_IMAGE_LONG = _lazy(
    "Please keep the length of your image filename to %(max)s "
    "characters or less. It is currently %(length)s characters."
)


class LimitedImageField(forms.ImageField):
    ALLOWED_IMAGE_EXTENSIONS = ("jpg", "jpeg", "png", "gif")
    default_validators = [FileExtensionValidator(allowed_extensions=ALLOWED_IMAGE_EXTENSIONS)]


class ImageAttachmentUploadForm(forms.Form):
    """Image upload form."""

    image = LimitedImageField(
        error_messages={"required": MSG_IMAGE_REQUIRED, "max_length": MSG_IMAGE_LONG},
        max_length=settings.MAX_FILENAME_LENGTH,
    )
