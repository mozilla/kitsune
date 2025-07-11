from django import forms
from django.conf import settings
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy as _lazy

from kitsune.groups.models import GroupProfile
from kitsune.sumo.form_fields import MultiUsernameField
from kitsune.sumo.widgets import ImageWidget
from kitsune.upload.forms import LimitedImageField
from kitsune.upload.utils import FileTooLargeError, check_file_size


class GroupProfileForm(forms.ModelForm):
    """The form for editing the group's profile."""

    class Meta:
        model = GroupProfile
        fields = ["information"]


class GroupAvatarForm(forms.ModelForm):
    """The form for editing the group's avatar."""

    avatar = LimitedImageField(required=True, widget=ImageWidget)

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request", None)
        super().__init__(*args, **kwargs)
        self.fields["avatar"].help_text = _("Your avatar will be resized to {size}x{size}").format(
            size=settings.AVATAR_SIZE
        )

    class Meta:
        model = GroupProfile
        fields = ["avatar"]

    def clean_avatar(self):
        """Validate the avatar file."""
        # Ensure an avatar file is attached
        if self.request.method == "POST":
            avatar = self.request.FILES.get("avatar")
            if not avatar:
                raise forms.ValidationError(_("You have not selected an image to upload."))
            # Validate file size
            try:
                check_file_size(avatar, settings.MAX_AVATAR_FILE_SIZE)
            except FileTooLargeError as e:
                raise forms.ValidationError(e.args[0])

        return self.cleaned_data["avatar"]


USERS_PLACEHOLDER = _lazy("username")


class AddUserForm(forms.Form):
    """Form to add members or leaders to group."""

    users = MultiUsernameField(
        widget=forms.TextInput(
            attrs={"placeholder": USERS_PLACEHOLDER, "class": "user-autocomplete"}
        )
    )
