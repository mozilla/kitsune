from django import forms

from tower import ugettext_lazy as _lazy

from kitsune.groups.models import GroupProfile
from kitsune.sumo.form_fields import MultiUsernameField
from kitsune.users.forms import AvatarForm


class GroupProfileForm(forms.ModelForm):
    """The form for editing the group's profile."""

    class Meta(object):
        model = GroupProfile
        fields = ['information']


# Inherit from user's AvatarForm but override the model.
class GroupAvatarForm(AvatarForm):
    """The form for editing the group's avatar."""

    class Meta(object):
        model = GroupProfile
        fields = ['avatar']


USERS_PLACEHOLDER = _lazy(u'username')


class AddUserForm(forms.Form):
    """Form to add members or leaders to group."""
    users = MultiUsernameField(
        widget=forms.TextInput(attrs={'placeholder': USERS_PLACEHOLDER,
                                      'class': 'user-autocomplete'}))
