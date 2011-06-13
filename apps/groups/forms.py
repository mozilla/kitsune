from django import forms

from groups.models import GroupProfile
from users.forms import AvatarForm


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
