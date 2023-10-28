from django import forms
from django.conf import settings
from django.utils.translation import gettext_lazy as _lazy

from kitsune.customercare.zendesk import ZendeskClient

PRODUCTS_WITH_OS = ["firefox-private-network-vpn"]

# See docs/zendesk.md for details about getting the valid choice values for each field:
CATEGORY_CHOICES = [
    (None, _lazy("Select a reason for contacting")),
    ("payment", _lazy("Payments & Billing")),
    ("accounts", _lazy("Accounts & Login")),
    ("technical", _lazy("Technical")),
    ("feedback", _lazy("Provide Feedback/Request Features")),
    ("not_listed", _lazy("Not listed")),
]

CATEGORY_CHOICES_LOGINLESS = [
    (None, _lazy("Select a reason for contacting")),
    ("fxa-reset-password", _lazy("I forgot my password")),
    ("fxa-emailverify-lockout", _lazy("I can't recover my account using email")),
    ("fxa-remove3rdprtylogin", _lazy("I'm having issues signing in with my Google or Apple ID")),
    ("fxa-2fa-lockout", _lazy("My security code isn't working or is lost")),
    ("other-account-issue", _lazy("I have another sign in issue")),
]

OS_CHOICES = [
    (None, _lazy("Select platform")),
    ("win10", _lazy("Windows")),
    ("mac", _lazy("Mac OS")),
    ("linux", _lazy("Linux")),
    ("android", _lazy("Android")),
    ("ios", _lazy("iOS")),
    ("other", _lazy("Other")),
]


class ZendeskForm(forms.Form):
    """Form for submitting a ticket to Zendesk."""

    required_css_class = "required"

    product = forms.CharField(disabled=True, widget=forms.HiddenInput)
    email = forms.EmailField(
        label=_lazy("Contact e-mail"), required=True, widget=forms.HiddenInput
    )
    category = forms.ChoiceField(
        label=_lazy("What do you need help with?"), required=True, choices=CATEGORY_CHOICES
    )
    os = forms.ChoiceField(
        label=_lazy("What operating system does your device use?"),
        choices=OS_CHOICES,
        required=False,
    )
    subject = forms.CharField(label=_lazy("Subject"), required=False)
    description = forms.CharField(
        label=_lazy("Tell us more"), widget=forms.Textarea(), required=False
    )
    country = forms.CharField(widget=forms.HiddenInput)

    def __init__(self, *args, product, user=None, **kwargs):
        kwargs.update({"initial": {"product": product.slug}})
        super().__init__(*args, **kwargs)
        if product.slug in settings.LOGIN_EXCEPTIONS and not user.is_authenticated:
            self.fields["email"].widget = forms.EmailInput()
            self.fields["category"].choices = CATEGORY_CHOICES_LOGINLESS
        else:
            self.fields["email"].initial = user.email
        self.label_suffix = ""

        if product.slug not in PRODUCTS_WITH_OS:
            del self.fields["os"]

    def send(self, user):
        client = ZendeskClient()
        return client.create_ticket(user, self.cleaned_data)
