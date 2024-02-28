from django import forms
from django.utils.translation import gettext_lazy as _lazy

from kitsune.sumo.form_fields import MultiGroupField, MultiUsernameField


class MessageForm(forms.Form):
    """Form send a private message."""

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super(MessageForm, self).__init__(*args, **kwargs)

        self.fields["to"] = MultiUsernameField(
            label=_lazy("To:"),
            widget=forms.TextInput(attrs={"class": "user-autocomplete"}),
            required=not self.user.profile.is_staff,
        )

        self.fields["to_group"] = forms.CharField(widget=forms.HiddenInput, required=False)
        self.fields["message"] = forms.CharField(
            label=_lazy("Message:"), max_length=10000, widget=forms.Textarea
        )
        self.fields["in_reply_to"] = forms.IntegerField(widget=forms.HiddenInput, required=False)

        if self.user and self.user.profile.is_staff:
            # Add the groups field only if the user is a privileged user
            self.fields["to_group"] = MultiGroupField(
                label=_lazy("To Group:"),
                widget=forms.TextInput(attrs={"class": "group-autocomplete"}),
                required=False,
            )

    def clean(self):
        cleaned_data = super().clean()

        if not cleaned_data.get("to_group") and not cleaned_data.get("to"):
            raise forms.ValidationError(_lazy("Either 'To' or 'To Group' must be provided."))

        return cleaned_data


class ReplyForm(forms.Form):
    """Form to reply to a private message."""

    to = forms.CharField(widget=forms.HiddenInput)
    message = forms.CharField(max_length=10000, widget=forms.Textarea)
    in_reply_to = forms.IntegerField(widget=forms.HiddenInput)
