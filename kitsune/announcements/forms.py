from datetime import date

from django import forms
from django.utils.translation import gettext_lazy as _lazy

from kitsune.products.models import Platform


class AnnouncementForm(forms.Form):
    """Form for collecting information about an announcement.

    This is not a ModelForm, and does not include the group or locale fields,
    because it should only be used in a context where the group or locale is
    implicit, and should not be user controllable. If you need a user
    controllable locale or group, use the admin interface.

    """

    content = forms.CharField(label=_lazy("Content"), max_length=10000, widget=forms.Textarea)
    show_after = forms.DateField(
        label=_lazy("Show after"), initial=date.today, input_formats=["%Y-%m-%d"]
    )
    show_until = forms.DateField(
        label=_lazy("Show until"), required=False, input_formats=["%Y-%m-%d"]
    )
    platforms = forms.ModelMultipleChoiceField(
        queryset=Platform.objects.filter(visible=True),
        label=_lazy("Target Platforms"),
        required=False,
        help_text=_lazy("Select platforms to target. Leave empty for site-wide announcements."),
        widget=forms.CheckboxSelectMultiple
    )
