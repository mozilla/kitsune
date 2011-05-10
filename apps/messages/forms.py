from django import forms
from django.contrib.auth.models import User

from tower import ugettext as _, ugettext_lazy as _lazy


TO_PLACEHOLDER = _lazy(u'username1, username2,...')


class MultiUsernameField(forms.Field):
    """Form field that takes a comma-separated list of usernames as input,
    validates that users exist for each one, and returns the list of users."""
    def to_python(self, value):
        if not value:
            raise forms.ValidationError(_lazy(u'To field is required.'))

        users = []
        for username in value.split(','):
            username = username.strip()
            try:
                user = User.objects.get(username=username)
                users.append(user)
            except User.DoesNotExist:
                msg = _('{username} is not a valid username.')
                raise forms.ValidationError(msg.format(username=username))
        return users


class MessageForm(forms.Form):
    """Form send a private message."""
    to = MultiUsernameField(
        widget=forms.TextInput(attrs={'placeholder': TO_PLACEHOLDER}))
    message = forms.CharField(max_length=3000, widget=forms.Textarea)
    in_reply_to = forms.IntegerField(widget=forms.HiddenInput, required=False)


class ReplyForm(forms.Form):
    """Form to reply to a private message."""
    to = forms.CharField(widget=forms.HiddenInput)
    message = forms.CharField(max_length=3000, widget=forms.Textarea)
    in_reply_to = forms.IntegerField(widget=forms.HiddenInput)
