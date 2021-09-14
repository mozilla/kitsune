from django import forms
from django.utils.translation import ugettext_lazy as _lazy

from kitsune.customercare.zendesk import ZendeskClient, CATEGORY_CHOICES, OS_CHOICES


class ZendeskForm(forms.Form):
    """Form for submitting a ticket to Zendesk."""

    product = forms.CharField(disabled=True, widget=forms.HiddenInput)
    category = forms.ChoiceField(
        label=_lazy("What do you need help with?"), choices=CATEGORY_CHOICES
    )
    os = forms.ChoiceField(
        label=_lazy("What operating system does your device use?"),
        choices=OS_CHOICES,
        required=False,
    )
    subject = forms.CharField(label=_lazy("Subject"), required=False)
    description = forms.CharField(label=_lazy("Description of issue"), widget=forms.Textarea())

    def __init__(self, *args, product, **kwargs):
        kwargs.update({"initial": {"product": product.slug}})
        super().__init__(*args, **kwargs)

    def send(self, user):
        client = ZendeskClient()
        return client.create_ticket(user, **self.cleaned_data)
