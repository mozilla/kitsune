import re

from django import forms
from django.conf import settings
from django.utils.translation import gettext_lazy as _lazy
from django.utils.translation import pgettext

from kitsune.customercare.models import accepted_context_for
from kitsune.customercare.utils import create_support_ticket
from kitsune.products.models import ZendeskTopicConfiguration

OS_CHOICES = [
    ("", _lazy("Select platform")),
    ("win64", _lazy("Windows 64-bit")),
    ("win_arm64", _lazy("Windows ARM64/AArch64")),
    ("win32", _lazy("Windows 32-bit")),
    ("mac", _lazy("macOS")),
    ("linux64", _lazy("Linux 64-bit")),
    ("linux_arm64", _lazy("Linux ARM64/AArch64")),
    ("linux32", _lazy("Linux 32-bit")),
    ("android", _lazy("Android")),
    ("ios", _lazy("iOS")),
]

UPDATE_CHANNEL_CHOICES = [
    ("", _lazy("Select update channel")),
    # L10n: "ESR" is short for Extended Support Release, a Firefox update channel.
    ("esr", _lazy("ESR")),
    ("rapid_release", _lazy("Rapid Release")),
    ("full_release", _lazy("Full Release")),
    ("beta", _lazy("Beta")),
    ("other", _lazy("Other")),
]

POLICY_DISTRIBUTION_CHOICES = [
    ("", _lazy("Select policy distribution method")),
    ("firefox_admin_console", _lazy("Firefox Enterprise Admin Console")),
    # L10n: Please don't translate "ADMX". It's a Windows file type.
    ("group_policy_admx", _lazy("Windows Group Policy (ADMX)")),
    # L10n: Please don't translate "Intune", "OMA-URI", or "ADMX". They're technical names.
    ("windows_mdm", _lazy("Windows MDM (Intune / OMA-URI / ADMX-backed)")),
    (
        "macos_config_profiles",
        # L10n: Please don't translate ".mobileconfig", ".plist", or "Jamf". The first two
        # are file types and Jamf is a product name.
        _lazy(
            "macOS Configuration Profiles (.mobileconfig / .plist, including MDM tools like Jamf)"
        ),
    ),
    # L10n: Please don't translate "policies.json". It's a file name.
    ("policies_json", _lazy("policies.json (manual deployment, all platforms)")),
    # L10n: Please don't translate "mozilla.cfg" or "autoconfig.js". They're file names.
    ("autoconfig", _lazy("Autoconfig (mozilla.cfg + autoconfig.js)")),
    ("not_sure", _lazy("Not sure / Need help selecting")),
]

URGENCY_CHOICES = [
    ("", _lazy("Select urgency")),
    (
        "normal",
        # L10n: Please don't translate "SEV3". It's a standard severity level name.
        _lazy("SEV3 (Normal) – Minor issue; no urgent business impact"),
    ),
    (
        "high",
        # L10n: Please don't translate "SEV2". It's a standard severity level name.
        _lazy("SEV2 (High) – Major degradation; workaround available"),
    ),
    (
        "critical",
        # L10n: Please don't translate "SEV1". It's a standard severity level name.
        _lazy("SEV1 (Critical) – Production outage or security risk"),
    ),
]

OS_TAGS = {
    "win64": "seg-platform-win64",
    "win_arm64": "seg-platform-win-arm64",
    "win32": "seg-platform-win32",
    "mac": "seg-platform-mac",
    "linux64": "seg-platform-linux64",
    "linux_arm64": "seg-platform-linux-arm64",
    "linux32": "seg-platform-linux32",
    "android": "seg-platform-android",
    "ios": "seg-platform-ios",
    "other": "seg-platform-other",
}

UPDATE_CHANNEL_TAGS = {
    "esr": "seg-rel-esr",
    "rapid_release": "seg-rel-rapid-release",
    "full_release": "seg-rel-full-release",
    "beta": "seg-rel-beta",
    "other": "seg-rel-channel-other",
}

POLICY_DISTRIBUTION_TAGS = {
    "firefox_admin_console": "seg-firefox-admin-console",
    "group_policy_admx": "seg-policy-windows-gpo",
    "windows_mdm": "seg-policy-windows-mdm",
    "macos_config_profiles": "seg-policy-macos-config-profiles",
    "policies_json": "seg-policy-json",
    "autoconfig": "seg-policy-autoconfig",
    "not_sure": "seg-policy-dist-other",
}

URGENCY_TAGS = {
    "normal": "seg-sev3",
    "high": "seg-sev2",
    "critical": "seg-sev1",
}


class ZendeskForm(forms.Form):
    """Form for submitting a ticket to Zendesk."""

    required_css_class = "required"

    email = forms.EmailField(
        label=_lazy("Contact e-mail"), required=True, widget=forms.HiddenInput
    )
    category = forms.ChoiceField(
        label=_lazy("What do you need help with?"), required=True, choices=[]
    )
    urgency = forms.ChoiceField(
        label=_lazy("What is the impact to your org?"),
        choices=URGENCY_CHOICES,
        widget=forms.HiddenInput,
        required=False,
    )
    os = forms.ChoiceField(
        label=_lazy("What operating system does your device use?"),
        choices=OS_CHOICES,
        required=False,
    )
    update_channel = forms.ChoiceField(
        label=_lazy("What update channel are you using?"),
        choices=UPDATE_CHANNEL_CHOICES,
        widget=forms.HiddenInput,
        required=False,
    )
    policy_distribution = forms.ChoiceField(
        # L10n: These are Firefox enterprise policies: settings that IT admins apply to
        # every copy of Firefox in their company.
        label=_lazy("How are you distributing policies?"),
        choices=POLICY_DISTRIBUTION_CHOICES,
        widget=forms.HiddenInput,
        required=False,
    )
    subject = forms.CharField(label=_lazy("Subject"), max_length=255)
    description = forms.CharField(label=_lazy("Tell us more"), widget=forms.Textarea())
    country = forms.CharField(widget=forms.HiddenInput, required=False, max_length=255)

    def __init__(self, *args, product, zendesk_config, coverage=None, user=None, **kwargs):
        super().__init__(*args, **kwargs)

        self.product = product
        self.zendesk_config = zendesk_config
        self.coverage = coverage
        self.user = user

        is_loginless = product.slug in settings.LOGIN_EXCEPTIONS and (
            not user or not user.is_authenticated
        )

        if is_loginless:
            self.fields["email"].widget = forms.EmailInput()
        else:
            self.fields["email"].initial = user.email
            self.fields["email"].disabled = True

        topic_configs = list(
            ZendeskTopicConfiguration.objects.filter(zendesk_config=zendesk_config)
            .select_related("zendesk_topic")
            .order_by("display_order")
        )
        self.topics = {config.zendesk_topic.slug: config.zendesk_topic for config in topic_configs}
        self.fields["category"].choices = [
            ("", _lazy("Select a reason for contacting")),
            *[
                (
                    config.zendesk_topic.slug,
                    pgettext(
                        "DB: products.ZendeskTopic.form_title", config.zendesk_topic.form_title
                    ),
                )
                for config in topic_configs
                if config.loginless_only == is_loginless
            ],
        ]

        for name, enabled in (
            ("os", zendesk_config.enable_os_field),
            ("update_channel", zendesk_config.enable_deployment_fields),
            ("policy_distribution", zendesk_config.enable_deployment_fields),
            ("urgency", zendesk_config.enable_urgency_field),
        ):
            field = self.fields[name]
            field.disabled = not enabled
            field.widget = forms.Select(choices=field.choices) if enabled else forms.HiddenInput()
            field.required = enabled and name != "os"

        self.label_suffix = ""

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if not email:
            return email

        if (
            ("@" in email and re.search(r"\.[a-zA-Z]{2,}\d+", email.split("@", 1)[1]))
            or email.count("@") != 1
            or " " in email
        ):
            raise forms.ValidationError(_lazy("Please enter a valid email address."))

        return email

    def send(self, user):
        """Create a SupportTicket record and trigger async classification."""
        zendesk_topic = self.topics.get(self.cleaned_data.get("category"))
        zendesk_tags = []

        if zendesk_topic:
            for tag_value in zendesk_topic.tags_dict.values():
                if tag_value:
                    if isinstance(tag_value, list):
                        zendesk_tags.extend(tag_value)
                    else:
                        zendesk_tags.append(tag_value)

        for field, tags in (
            ("os", OS_TAGS),
            ("update_channel", UPDATE_CHANNEL_TAGS),
            ("policy_distribution", POLICY_DISTRIBUTION_TAGS),
            ("urgency", URGENCY_TAGS),
        ):
            if tag := tags.get(self.cleaned_data.get(field)):
                zendesk_tags.append(tag)

        if settings.STAGE:
            zendesk_tags.append("stage")

        accepted_context = accepted_context_for(
            self.product, self.zendesk_config, self.coverage, topics=self.topics.values()
        )
        accepted_context["selected_topic_id"] = zendesk_topic.topic_id if zendesk_topic else None
        return create_support_ticket(
            user if (user and user.is_authenticated) else None,
            self.product,
            subject=self.cleaned_data["subject"],
            description=self.cleaned_data["description"],
            category=self.cleaned_data.get("category", ""),
            email=self.cleaned_data["email"],
            os=self.cleaned_data.get("os", ""),
            country=self.cleaned_data.get("country", ""),
            update_channel=self.cleaned_data.get("update_channel", ""),
            policy_distribution=self.cleaned_data.get("policy_distribution", ""),
            urgency=self.cleaned_data.get("urgency", ""),
            zendesk_tags=zendesk_tags,
            coverage=self.coverage,
            accepted_context=accepted_context,
        )


class SupportTicketReplyForm(forms.Form):
    """Form for a ticket owner to author a reply that will be posted to Zendesk."""

    body = forms.CharField(
        label=_lazy("Reply"),
        widget=forms.Textarea,
        max_length=65_535,
        error_messages={
            "required": _lazy("Please enter a reply."),
            "max_length": _lazy("Replies are limited to %(limit_value)d characters."),
        },
    )

    def __init__(self, *args, placeholder=None, **kwargs):
        super().__init__(*args, **kwargs)
        if placeholder:
            self.fields["body"].widget.attrs["placeholder"] = placeholder
