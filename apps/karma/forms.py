from django import forms

from karma.manager import KarmaManager


class UserAPIForm(forms.Form):
    """Form for the user API view.

    * Validates the query string parameters."""
    daterange = forms.ChoiceField(
        required=False,
        choices=[(k, k) for k in KarmaManager.date_ranges.keys() + ['all']])
    sort = forms.ChoiceField(
        required=False,
        choices=[(k, k) for k
                 in KarmaManager.action_types.keys() + ['points']])
    page = forms.IntegerField(required=False)
    pagesize = forms.IntegerField(required=False)


class OverviewAPIForm(forms.Form):
    """Form for the overview API view.

    * Validates the query string parameters."""
    daterange = forms.ChoiceField(
        required=False,
        choices=[(k, k) for k in KarmaManager.date_ranges.keys() + ['all']])
