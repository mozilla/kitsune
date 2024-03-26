from django import forms
from django.utils.translation import gettext_lazy as _lazy

from kitsune.sumo.form_fields import MultiUsernameOrGroupnameField


class MessageForm(forms.Form):
    """Form send a private message."""

    to = MultiUsernameOrGroupnameField(
        label=_lazy("To:"),
        widget=forms.TextInput(attrs={"class": "user-autocomplete"}),
    )
    to_group = forms.CharField(
        label=_lazy("To group:"),
        widget=forms.HiddenInput(),
        required=False,
    )
    message = forms.CharField(label=_lazy("Message:"), max_length=10000, widget=forms.Textarea)
    in_reply_to = forms.IntegerField(widget=forms.HiddenInput, required=False)


class ReplyForm(forms.Form):
    """Form to reply to a private message."""

    to = forms.CharField(widget=forms.HiddenInput)
    to_group = forms.CharField(
        label=_lazy("To group:"),
        widget=forms.HiddenInput(),
        required=False,
    )
    message = forms.CharField(max_length=10000, widget=forms.Textarea)
    in_reply_to = forms.IntegerField(widget=forms.HiddenInput)
