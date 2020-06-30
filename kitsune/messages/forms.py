from django import forms
from django.utils.translation import ugettext_lazy as _lazy

from kitsune.sumo.form_fields import MultiUsernameField


TO_PLACEHOLDER = _lazy("username1, username2,...")


class MessageForm(forms.Form):
    """Form send a private message."""

    to = MultiUsernameField(
        label=_lazy("To:"),
        widget=forms.TextInput(
            attrs={"placeholder": TO_PLACEHOLDER, "class": "user-autocomplete"}
        ),
    )
    message = forms.CharField(label=_lazy("Message:"), max_length=10000, widget=forms.Textarea)
    in_reply_to = forms.IntegerField(widget=forms.HiddenInput, required=False)


class ReplyForm(forms.Form):
    """Form to reply to a private message."""

    to = forms.CharField(widget=forms.HiddenInput)
    message = forms.CharField(max_length=10000, widget=forms.Textarea)
    in_reply_to = forms.IntegerField(widget=forms.HiddenInput)
