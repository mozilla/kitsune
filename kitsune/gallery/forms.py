from django import forms
from django.conf import settings
from django.utils.translation import ugettext_lazy as _lazy, ugettext as _

from kitsune.gallery.models import Image
from kitsune.lib.sumo_locales import LOCALES
from kitsune.upload.forms import LimitedImageField

# Error messages
MSG_TITLE_REQUIRED = _lazy("Please provide a title.")
MSG_TITLE_SHORT = _lazy(
    "The title is too short (%(show_value)s characters). It must be at "
    "least %(limit_value)s characters."
)
MSG_TITLE_LONG = _lazy(
    "Please keep the length of your title to %(limit_value)s characters "
    "or less. It is currently %(show_value)s characters."
)
MSG_DESCRIPTION_REQUIRED = _lazy("Please provide a description.")
MSG_DESCRIPTION_LONG = _lazy(
    "Please keep the length of your description to %(limit_value)s "
    "characters or less. It is currently %(show_value)s characters."
)
MSG_IMAGE_REQUIRED = _lazy("You have not selected an image to upload.")
MSG_IMAGE_LONG = _lazy(
    "Please keep the length of your image filename to %(max)s "
    "characters or less. It is currently %(length)s characters."
)
MSG_TITLE_DRAFT = _lazy("Please select a different title.")

TITLE_HELP_TEXT = _lazy("Include this in wiki syntax with [[Image:title]]")
DESCRIPTION_HELP_TEXT = _lazy("Provide a brief description of this media.")


class MediaForm(forms.ModelForm):
    """Common abstractions for Image form."""

    locale = forms.ChoiceField(
        required=False,
        label=_lazy("Locale"),
        choices=[(k, LOCALES[k].native) for k in settings.SUMO_LANGUAGES],
        initial=settings.WIKI_DEFAULT_LANGUAGE,
    )
    title = forms.CharField(
        required=False,
        label=_lazy("Title"),
        help_text=TITLE_HELP_TEXT,
        min_length=5,
        max_length=255,
        error_messages={
            "required": MSG_TITLE_REQUIRED,
            "min_length": MSG_TITLE_SHORT,
            "max_length": MSG_TITLE_LONG,
        },
    )
    description = forms.CharField(
        required=False,
        label=_lazy("Description"),
        help_text=DESCRIPTION_HELP_TEXT,
        max_length=10000,
        widget=forms.Textarea(),
        error_messages={"required": MSG_DESCRIPTION_REQUIRED, "max_length": MSG_DESCRIPTION_LONG},
    )

    def __init__(self, *args, **kwargs):
        self.is_ajax = kwargs.pop("is_ajax", True)
        super(MediaForm, self).__init__(*args, **kwargs)
        if not self.is_ajax:
            self.fields["locale"].required = True
            self.fields["title"].required = True
            self.fields["description"].required = True

    def save(self, update_user=None, is_draft=True, **kwargs):
        return save_form(self, update_user, is_draft=is_draft, **kwargs)


class ImageForm(MediaForm):
    """Image form."""

    file = LimitedImageField(
        error_messages={"required": MSG_IMAGE_REQUIRED, "max_length": MSG_IMAGE_LONG},
        label=_lazy("Image"),
        max_length=settings.MAX_FILENAME_LENGTH,
        widget=forms.FileInput(attrs={"accept": "image/*, video/*"}),
    )

    def __init__(self, *args, **kwargs):
        super(ImageForm, self).__init__(*args, **kwargs)
        msg = _(
            "Accepted formats include: PNG, JPEG, GIF. "
            '<a target="_blank" href="{learn_more}">Learn more...</a>'
        )
        url = "http://infohost.nmt.edu/tcc/help/pubs/pil/formats.html"
        self.fields["file"].help_text = msg.format(learn_more=url)

    class Meta:
        model = Image
        fields = ("file", "locale", "title", "description")


def save_form(form, update_user=None, is_draft=True, **kwargs):
    """Save a media form, add user to updated_by.

    Warning: this assumes you're calling it from a subclass of MediaForm.

    """
    obj = super(MediaForm, form).save(commit=False, **kwargs)
    if update_user:
        obj.updated_by = update_user
    obj.is_draft = is_draft
    obj.save()
    return obj
