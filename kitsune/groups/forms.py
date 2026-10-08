from django import forms
from django.conf import settings
from django.contrib.auth.models import Group
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy as _lazy

from kitsune.groups.membership import validate_enterprise_memberships
from kitsune.groups.models import GroupProfile
from kitsune.sumo.form_fields import MultiUsernameField
from kitsune.sumo.widgets import ImageWidget
from kitsune.upload.forms import LimitedImageField
from kitsune.upload.utils import validate_avatar_size


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
        self.fields["avatar"].help_text = _(
            "Upload an image file (JPG or PNG). Maximum file size: {size}MB"
        ).format(size=settings.MAX_AVATAR_FILE_SIZE // (1024 * 1024))

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
            validate_avatar_size(avatar)

        return self.cleaned_data["avatar"]


USERS_PLACEHOLDER = _lazy("username")


class AddUserForm(forms.Form):
    """Form to add members or leaders to group."""

    users = MultiUsernameField(
        widget=forms.TextInput(
            attrs={"placeholder": USERS_PLACEHOLDER, "class": "user-autocomplete"}
        )
    )

    def __init__(self, *args, group=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.group = group

    def clean_users(self):
        users = self.cleaned_data["users"]
        if self.group is not None:
            validate_enterprise_memberships([user.pk for user in users], [self.group.pk])
        return users


class EnterpriseCompanyForm(forms.Form):
    name = forms.CharField(
        label=_lazy("Company name"),
        max_length=Group._meta.get_field("name").max_length,
    )
    include_live_chat = forms.BooleanField(
        label=_lazy("Include live chat"),
        required=False,
        help_text=_lazy("Requires live chat to be enabled and configured for this site."),
    )
    zendesk_organization_id = forms.RegexField(
        label=_lazy("Existing Zendesk organization ID"),
        regex=r"^[0-9]+$",
        max_length=255,
        required=False,
        help_text=_lazy(
            "Optional. Link an existing organization by ID. Once linked, it cannot be changed."
        ),
        error_messages={"invalid": _lazy("Enter a positive numeric organization ID.")},
    )

    def __init__(self, *args, company=None, linked_organization_id=None, **kwargs):
        super().__init__(*args, **kwargs)
        if company is not None:
            del self.fields["name"]
        if linked_organization_id:
            field = self.fields["zendesk_organization_id"]
            field.initial = linked_organization_id
            field.disabled = True

    def clean_zendesk_organization_id(self):
        value = self.cleaned_data["zendesk_organization_id"]
        if value and int(value) <= 0:
            raise forms.ValidationError(_("Enter a positive numeric organization ID."))
        return value or None
