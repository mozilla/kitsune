from django import forms
from django.conf import settings
from django.utils.translation import gettext_lazy as _lazy

from kitsune.customercare import ZENDESK_CATEGORIES, ZENDESK_CATEGORIES_LOGINLESS
from kitsune.customercare.zendesk import ZendeskClient
from kitsune.products import PRODUCT_SLUG_ALIASES

PRODUCTS_WITH_OS = ["mozilla-vpn"]

OS_CHOICES = [
    (None, _lazy("Select platform")),
    ("win10", _lazy("Windows")),
    ("mac", _lazy("Mac OS")),
    ("linux", _lazy("Linux")),
    ("android", _lazy("Android")),
    ("ios", _lazy("iOS")),
    ("other", _lazy("Other")),
]

ZENDESK_PRODUCT_SLUGS = {v: k for k, v in PRODUCT_SLUG_ALIASES.items()}


class ZendeskForm(forms.Form):
    """Form for submitting a ticket to Zendesk."""

    required_css_class = "required"

    email = forms.EmailField(
        label=_lazy("Contact e-mail"), required=True, widget=forms.HiddenInput
    )
    category = forms.ChoiceField(
        label=_lazy("What do you need help with?"), required=True, choices=[]
    )
    os = forms.ChoiceField(
        label=_lazy("What operating system does your device use?"),
        choices=OS_CHOICES,
        required=False,
    )
    subject = forms.CharField(label=_lazy("Subject"))
    description = forms.CharField(label=_lazy("Tell us more"), widget=forms.Textarea())
    country = forms.CharField(widget=forms.HiddenInput, required=False)

    def __init__(self, *args, product, user=None, **kwargs):
        super().__init__(*args, **kwargs)

        self.product = product
        self.user = user

        if product.slug in settings.LOGIN_EXCEPTIONS and not user.is_authenticated:
            self.fields["email"].widget = forms.EmailInput()
            categories_dict = ZENDESK_CATEGORIES_LOGINLESS
        else:
            self.fields["email"].initial = user.email
            categories_dict = ZENDESK_CATEGORIES

        self.product_categories = categories_dict.get(product.slug, [])

        category_choices = [(None, _lazy("Select a reason for contacting"))]
        for category in self.product_categories:
            category_choices.append((category["slug"], category["topic"]))

        self.fields["category"].choices = category_choices
        self.label_suffix = ""
        if product.slug not in PRODUCTS_WITH_OS:
            self.fields["os"].widget = forms.HiddenInput()

    def send(self, user, product):
        client = ZendeskClient()
        zendesk_product = (
            ZENDESK_PRODUCT_SLUGS.get(product.slug, product.slug)
            if product.slug == "mozilla-vpn"
            else product.slug
        )
        self.cleaned_data["product"] = zendesk_product
        self.cleaned_data["product_title"] = product.title

        selected_category_slug = self.cleaned_data.get("category")
        if selected_category_slug:
            selected_category_data = None
            for category in self.product_categories:
                if category["slug"] == selected_category_slug:
                    selected_category_data = category
                    break

            if selected_category_data:
                tags = []
                tag_data = selected_category_data["tags"]

                for tag_value in tag_data.values():
                    if tag_value:
                        if isinstance(tag_value, list):
                            tags.extend(tag_value)
                        else:
                            tags.append(tag_value)

                self.cleaned_data["zendesk_tags"] = tags
        return client.create_ticket(user, self.cleaned_data)
