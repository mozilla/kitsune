from django import forms

from groups.models import GroupProfile


class GroupProfileForm(forms.ModelForm):
    """The form for editing the group's profile."""

    class Meta(object):
        model = GroupProfile
        fields = ['information']
