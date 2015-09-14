from django import forms


class SearchForm(forms.Form):
    """Django form for handling display and validation"""
    query = forms.CharField(required=False)
