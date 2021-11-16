from django import forms
from django.utils.translation import ugettext_lazy as _lazy

from kitsune.customercare.zendesk import CATEGORY_CHOICES, OS_CHOICES, ZendeskClient

PRODUCTS_WITH_OS = ["firefox-private-network-vpn"]


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
    description = forms.CharField(label=_lazy("Your message"), widget=forms.Textarea())
    country = forms.CharField(widget=forms.HiddenInput)

    def __init__(self, *args, product, **kwargs):
        kwargs.update({"initial": {"product": product.slug}})
        super().__init__(*args, **kwargs)
        if product.slug not in PRODUCTS_WITH_OS:
            del self.fields["os"]

    def send(self, user):
        client = ZendeskClient()
        return client.create_ticket(user, self.cleaned_data)
