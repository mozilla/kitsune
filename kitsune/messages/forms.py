from django import forms
from django.contrib.auth.models import Group
from django.utils.translation import gettext_lazy as _lazy

from kitsune.sumo.form_fields import MultiUsernameOrGroupnameField


class MessageForm(forms.Form):
    """Form send a private message."""

    to = MultiUsernameOrGroupnameField(
        label=_lazy("To:"),
        widget=forms.TextInput(
            attrs={"placeholder": _lazy("Search for Users"), "class": "user-autocomplete"}
        ),
    )
    message = forms.CharField(label=_lazy("Message:"), max_length=10000, widget=forms.Textarea)
    in_reply_to = forms.IntegerField(widget=forms.HiddenInput, required=False)

    def __init__(self, *args, **kwargs):
        # Grab the user
        self.user = kwargs.pop("user")
        super(MessageForm, self).__init__(*args, **kwargs)

        # If the user is a member of the staff group, the placholder text needs to be updated.
        if self.user and self.user.profile.in_staff_group:
            self.fields["to"].widget.attrs["placeholder"] = _lazy("Search for Users or Groups")

    def clean_to(self):
        """Ensure that all usernames and group names are valid."""
        to = self.cleaned_data.get("to", {})

        # Check if there are valid users or groups selected.
        if not to.get("users") and not to.get("groups"):
            raise forms.ValidationError(_lazy("Please select at least one user or group."))

        # Check for group messages permissions.
        if to.get("groups"):
            # If the user is not a member of the staff group,
            # they are not allowed to send messages to groups.
            if not self.user.profile.in_staff_group:
                raise forms.ValidationError(
                    _lazy("You are not allowed to send messages to groups.")
                )
            # If the group lacks a profile, the user is not allowed to send messages to it.
            group_names = to.get("groups")
            if bad_group_names := (
                set(group_names)
                - set(
                    Group.objects.filter(name__in=group_names, profile__isnull=False).values_list(
                        "name", flat=True
                    )
                )
            ):
                raise forms.ValidationError(
                    # L10n: This message is shown when the user tries to send a message to a group
                    # L10n: but that group doesn't have a profile.
                    _lazy(
                        "You are not allowed to send messages to groups that don't have profiles."
                    )
                    + f"({', '.join(bad_group_names)})."
                )

        return to


class ReplyForm(forms.Form):
    """Form to reply to a private message."""

    to = forms.CharField(widget=forms.HiddenInput)
    message = forms.CharField(max_length=10000, widget=forms.Textarea)
    in_reply_to = forms.IntegerField(widget=forms.HiddenInput)
