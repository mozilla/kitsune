from django import forms
from django.conf import settings
from django.utils.translation import gettext_lazy as _lazy

from kitsune import search as constants
from kitsune.lib.sumo_locales import LOCALES
from kitsune.products.models import Product

MAX_QUERY_LENGTH = 200
SEARCH_LANGUAGES = [(k, LOCALES[k].native) for k in settings.SUMO_LANGUAGES]


class BaseSearchForm(forms.Form):
    q = forms.CharField(required=True, max_length=MAX_QUERY_LENGTH)

    w = forms.TypedChoiceField(
        required=False,
        coerce=int,
        widget=forms.HiddenInput,
        empty_value=constants.WHERE_BASIC,
        choices=(
            (constants.WHERE_SUPPORT, None),
            (constants.WHERE_WIKI, None),
            (constants.WHERE_BASIC, None),
            (constants.WHERE_DISCUSSION, None),
        ),
    )


class SimpleSearchForm(BaseSearchForm):
    """Django form to handle the simple search case."""

    explain = forms.BooleanField(required=False)
    all_products = forms.BooleanField(required=False)
    language = forms.CharField(required=False)

    product = forms.MultipleChoiceField(
        required=False, label=_lazy("Relevant to"), widget=forms.CheckboxSelectMultiple()
    )

    def __init__(self, *args, **kwargs):
        super(SimpleSearchForm, self).__init__(*args, **kwargs)

        product_field = self.fields["product"]
        product_field.choices = Product.objects.values_list("slug", "title")

    def clean_products(self):
        products = self.cleaned_data["products"]
        # If products were specified or all_products was set, then we return
        # the products as is.
        if products or self.cleaned_data["all_products"]:
            return products

        # If no products were specified and we're not looking for all_products,
        # then populate products by looking at things in the query.
        lowered_q = self.cleaned_data["q"].lower()

        if "thunderbird" in lowered_q:
            products.append("thunderbird")
        elif "android" in lowered_q:
            products.append("mobile")
        elif (
            "ios" in lowered_q
            or "ipad" in lowered_q
            or "ipod" in lowered_q
            or "iphone" in lowered_q
        ):
            products.append("ios")
        elif "firefox" in lowered_q:
            products.append("firefox")
        return products
