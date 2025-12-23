import re

from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.validators import validate_email
from django.utils.translation import gettext_lazy as _lazy

from kitsune.customercare.models import SupportTicket
from kitsune.products import PRODUCT_SLUG_ALIASES
from kitsune.products.models import ProductSupportConfig, ZendeskTopic, ZendeskTopicConfiguration

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

        is_loginless = product.slug in settings.LOGIN_EXCEPTIONS and (
            not user or not user.is_authenticated
        )

        if is_loginless:
            self.fields["email"].widget = forms.EmailInput()
        else:
            self.fields["email"].initial = user.email

        try:
            support_config = ProductSupportConfig.objects.get(product=product, is_active=True)
        except ProductSupportConfig.DoesNotExist:
            support_config = None

        if support_config and support_config.zendesk_config:
            zendesk_config = support_config.zendesk_config

            topic_configs = ZendeskTopicConfiguration.objects.filter(
                zendesk_config=zendesk_config,
                loginless_only=is_loginless
            ).select_related("zendesk_topic").order_by("display_order")

            category_choices = [(None, _lazy("Select a reason for contacting"))]
            for topic_config in topic_configs:
                topic = topic_config.zendesk_topic
                category_choices.append((topic.slug, topic.topic))

            self.fields["category"].choices = category_choices

            if not zendesk_config.enable_os_field:
                self.fields["os"].widget = forms.HiddenInput()

        self.label_suffix = ""

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
            try:
                support_config = ProductSupportConfig.objects.get(product=product, is_active=True)
            except ProductSupportConfig.DoesNotExist:
                support_config = None

            if support_config and support_config.zendesk_config:
                try:
                    topic = ZendeskTopic.objects.get(slug=selected_category_slug)
                except ZendeskTopic.DoesNotExist:
                    topic = None

                if topic:
                    tag_data = topic.tags_dict

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

        from kitsune.customercare.tasks import zendesk_submission_classifier

        zendesk_submission_classifier.delay(submission.id)

        return submission
