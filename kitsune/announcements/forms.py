from datetime import date

from django import forms

from tower import ugettext_lazy as _lazy


class AnnouncementForm(forms.Form):
    """Form for collecting information about an announcement.

    This is not a ModelForm, and does not include the group or locale fields,
    because it should only be used in a context where the group or locale is
    implicit, and should not be user controllable. If you need a user
    controllable locale or group, use the admin interface.

    """
    content = forms.CharField(label=_lazy(u'Content'), max_length=10000,
                              widget=forms.Textarea)
    show_after = forms.DateField(label=_lazy(u'Show after'),
                                 initial=date.today,
                                 input_formats=['%Y-%m-%d'])
    show_until = forms.DateField(label=_lazy(u'Show until'), required=False,
                                 input_formats=['%Y-%m-%d'])
