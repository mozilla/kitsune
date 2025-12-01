import re

from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.validators import validate_email
from django.utils.translation import gettext_lazy as _lazy

from kitsune.customercare import ZENDESK_CATEGORIES, ZENDESK_CATEGORIES_LOGINLESS
from kitsune.customercare.models import SupportTicket
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

        if product.slug in settings.LOGIN_EXCEPTIONS and (not user or not user.is_authenticated):
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

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if not email:
            return email

        is_invalid = False

        try:
            validate_email(email)
        except DjangoValidationError:
            is_invalid = True

        if re.search(r"\.[a-zA-Z]{2,}\d+", email):
            is_invalid = True

        if email.count("@") != 1 or " " in email:
            is_invalid = True

        if is_invalid:
            raise forms.ValidationError(_lazy("Please enter a valid email address."))

        return email

    def send(self, user, product):
        """Create a SupportTicket record and trigger async classification."""
        selected_category_slug = self.cleaned_data.get("category")
        zendesk_tags = []
        if selected_category_slug:
            selected_category_data = None
            for category in self.product_categories:
                if category["slug"] == selected_category_slug:
                    selected_category_data = category
                    break

            if selected_category_data:
                tag_data = selected_category_data["tags"]

                for tag_value in tag_data.values():
                    if tag_value:
                        if isinstance(tag_value, list):
                            zendesk_tags.extend(tag_value)
                        else:
                            zendesk_tags.append(tag_value)

        if settings.STAGE:
            zendesk_tags.append("stage")

        submission = SupportTicket.objects.create(
            subject=self.cleaned_data["subject"],
            description=self.cleaned_data["description"],
            category=self.cleaned_data.get("category", ""),
            email=self.cleaned_data["email"],
            os=self.cleaned_data.get("os", ""),
            country=self.cleaned_data.get("country", ""),
            product=product,
            user=user if (user and user.is_authenticated) else None,
            zendesk_tags=zendesk_tags,
            status=SupportTicket.STATUS_PENDING,
        )

        # Trigger async classification task
        from kitsune.customercare.tasks import zendesk_submission_classifier

        zendesk_submission_classifier.delay(submission.id)

        return submission
