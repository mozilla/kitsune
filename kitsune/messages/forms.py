from django import forms
from django.utils.translation import gettext_lazy as _lazy

from kitsune.sumo.form_fields import MultiUsernameOrGroupnameField


class MessageForm(forms.Form):
    """Form send a private message."""

    to = MultiUsernameOrGroupnameField(
        label=_lazy("To:"),
        widget=forms.TextInput(
            attrs={"placeholder": "Search for Users", "class": "user-autocomplete"}
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
            self.fields["to"].widget.attrs["placeholder"] = "Search for Users or Groups"

    def clean_to(self):
        """Ensure that all usernames and group names are valid."""
        to = self.cleaned_data["to"]

        if not to["users"] and not to["groups"]:
            raise forms.ValidationError("Please select at least one user or group.")
        if to["groups"] and not self.user.profile.in_staff_group:
            raise forms.ValidationError("You are not allowed to send messages to groups.")

        return to


class ReplyForm(forms.Form):
    """Form to reply to a private message."""

    to = forms.CharField(widget=forms.HiddenInput)
    message = forms.CharField(max_length=10000, widget=forms.Textarea)
    in_reply_to = forms.IntegerField(widget=forms.HiddenInput)
