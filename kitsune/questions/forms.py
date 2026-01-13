import html
import json

from django import forms
from django.contrib.contenttypes.models import ContentType
from django.utils.html import strip_tags
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy as _lazy

from kitsune.products.models import Topic
from kitsune.questions.events import QuestionReplyEvent
from kitsune.questions.models import AAQConfig, Answer, Question
from kitsune.questions.utils import remove_pii
from kitsune.sumo.forms import KitsuneBaseForumForm
from kitsune.upload.models import ImageAttachment

# unused labels and help text
# L10n: Unused. A label for a field, displayed when filing a question form (e.g., on https://support.mozilla.org/questions/new/firefox/form).
SITE_AFFECTED_LABEL = _lazy("URL of affected site")
# L10n: Unused. A label for a field, displayed when filing a question form (e.g., on https://support.mozilla.org/questions/new/firefox/form).
CRASH_ID_LABEL = _lazy("Crash ID(s)")
# if you want to use the following string, update it to remove "en-US" from the link first
# when updating, don't remove the original string, just mark it as deprecated and create a new one
# L10n: Unused. A description of the "Crash ID(s)" field, displayed when filing a question form (e.g., on https://support.mozilla.org/questions/new/firefox/form).
CRASH_ID_HELP = _lazy("If you submit information to Mozilla when you crash, you'll be given a crash ID which uniquely identifies your crash and lets us look at details that may help identify the cause. To find your recently submitted crash IDs, go to <strong>about:crashes</strong> in your location bar. <a href='https://support.mozilla.com/en-US/kb/Firefox+crashes#Getting_the_most_accurate_help_with_your_Firefox_crash' target='_blank'>Click for detailed instructions</a>.")
# L10n: Unused. A label for a field, displayed when filing a question form (e.g., on https://support.mozilla.org/questions/new/firefox/form).
FREQUENCY_LABEL = _lazy("This happens")
FREQUENCY_CHOICES = [
    ("", ""),
    # L10n: Unused. An option for the "This happens" field, displayed when filing a question form (e.g., on https://support.mozilla.org/questions/new/firefox/form).
    ("NOT_SURE", _lazy("Not sure how often")),
    # L10n: Unused. An option for the "This happens" field, displayed when filing a question form (e.g., on https://support.mozilla.org/questions/new/firefox/form).
    ("ONCE_OR_TWICE", _lazy("Just once or twice")),
    # L10n: Unused. An option for the "This happens" field, displayed when filing a question form (e.g., on https://support.mozilla.org/questions/new/firefox/form).
    ("FEW_TIMES_WEEK", _lazy("A few times a week")),
    # L10n: Unused. An option for the "This happens" field, displayed when filing a question form (e.g., on https://support.mozilla.org/questions/new/firefox/form).
    ("EVERY_TIME", _lazy("Every time Firefox opened")),
]
# L10n: Unused. A label for a field, displayed when filing a question form (e.g., on https://support.mozilla.org/questions/new/firefox/form).
STARTED_LABEL = _lazy("This started when...")
# L10n: Unused. A label for a field, displayed when filing a question form (e.g., on https://support.mozilla.org/questions/new/firefox/form).
PLUGINS_LABEL = _lazy("Installed plugins")
# L10n: Unused. A label for a field, displayed when filing a question form (e.g., on https://support.mozilla.org/questions/new/firefox/form).
ADDON_LABEL = _lazy("Extension/plugin you are having trouble with")
# L10n: Unused. A label for a field, displayed when filing a question form (e.g., on https://support.mozilla.org/questions/new/firefox/form).
DEVICE_LABEL = _lazy("Mobile device")

# unused labels and help text
# L10n: A label for a field, displayed when filing a question form (e.g., on https://support.mozilla.org/questions/new/firefox/form).
TROUBLESHOOTING_LABEL = _lazy("Troubleshooting Information")
# L10n: A description of the "Troubleshooting Information" field, displayed when filing a question form (e.g., on https://support.mozilla.org/questions/new/firefox/form).
TROUBLESHOOTING_HELP = _lazy("This information gives details about the internal workings of your browser that will help in answering your question.")
# L10n: A label for a field, displayed when filing a question form (e.g., on https://support.mozilla.org/questions/new/firefox/form).
TITLE_LABEL = _lazy("Summarize your question")
# L10n: A description of the "Summarize your question" field, displayed when filing a question form (e.g., on https://support.mozilla.org/questions/new/firefox/form).
TITLE_HELP_TEXT = _lazy("Please summarize your question in one sentence:")
# L10n: A label for a field, displayed when filing a question form (e.g., on https://support.mozilla.org/questions/new/firefox/form).
CONTENT_LABEL = _lazy("How can we help?")
# L10n: A description of the "How can we help?" field, displayed when filing a question form (e.g., on https://support.mozilla.org/questions/new/firefox/form).
CONTENT_HELP_TEXT = _lazy('Please include as much detail as possible. Also, remember to follow our <a href="https://support.mozilla.org/kb/mozilla-support-rules-guidelines" target="_blank">rules and guidelines</a>.')
# L10n: A label for a field, displayed when filing a Firefox-related question form (e.g., on https://support.mozilla.org/questions/new/firefox/form).
FF_VERSION_LABEL = _lazy("Firefox version")
# L10n: A label for a field, displayed when filing a Thunderbird-related question form (e.g., on https://support.mozilla.org/questions/new/thunderbird/form).
TB_VERSION_LABEL = _lazy("Thunderbird version")
# L10n: A placeholder for the "Thunderbird version" field, displayed when filing a Thunderbird-related question form (e.g., on https://support.mozilla.org/questions/new/thunderbird/form).
TB_VERSION_PLACEHOLDER = _lazy("e.g., 140.5.0esr, 146.1.0 release or 147.0b4")
# L10n: A label for a field, displayed when filing a question form (e.g., on https://support.mozilla.org/questions/new/firefox/form).
OS_LABEL = _lazy("Operating system")
# L10n: A label for a field, displayed when filing a question form (e.g., on https://support.mozilla.org/questions/new/firefox/form).
CATEGORY_LABEL = _lazy("Which topic best describes your question?")
# L10n: A label for a checkbox, displayed when filing a question form (e.g., on https://support.mozilla.org/questions/new/firefox/form).
NOTIFICATIONS_LABEL = _lazy("Email me when someone answers the thread")

# L10n: A placeholder for the "Post a Reply" editor.
REPLY_PLACEHOLDER = _lazy("Enter your reply here.")
# L10n: A placeholder for the email field, displayed when subscribing to a question while not signed in.
EMAIL_PLACEHOLDER = _lazy("Enter your email address here.")


class EditQuestionForm(forms.ModelForm):
    """Form to edit an existing question"""

    title = forms.CharField(label=TITLE_LABEL, help_text=TITLE_HELP_TEXT, min_length=5)

    content = forms.CharField(label=CONTENT_LABEL, help_text=CONTENT_HELP_TEXT, min_length=5, widget=forms.Textarea())

    class Meta:
        model = Question
        fields = ["title", "content"]

    def __init__(self, product=None, *args, **kwargs):
        """Init the form.

        We are adding fields here and not declaratively because the
        form fields to include depend on the selected product/category.
        """
        super().__init__(*args, **kwargs)
        self.label_suffix = None

        #  Extra fields required by product/category selected
        extra_fields = []

        if product:
            aaq_config = AAQConfig.objects.get(product=product, is_active=True)
            extra_fields = aaq_config.extra_fields

        if "ff_version" in extra_fields:
            self.fields["ff_version"] = forms.CharField(
                label=FF_VERSION_LABEL,
                required=False,
            )

        if "tb_version" in extra_fields:
            self.fields["tb_version"] = forms.CharField(
                label=TB_VERSION_LABEL,
                required=False,
                widget=forms.TextInput(attrs={"placeholder": TB_VERSION_PLACEHOLDER}),
            )

        if "os" in extra_fields:
            self.fields["os"] = forms.CharField(
                label=OS_LABEL,
                required=False,
            )

        if "troubleshooting" in extra_fields:
            widget = forms.Textarea(attrs={"class": "troubleshooting"})
            field = forms.CharField(
                label=TROUBLESHOOTING_LABEL,
                help_text=TROUBLESHOOTING_HELP,
                required=False,
                max_length=655360,
                widget=widget,
            )
            self.fields["troubleshooting"] = field

        for field in self.fields.values():
            if not field.required:
                # L10n: A label suffix for optional fields, displayed when filing a question form (e.g., on https://support.mozilla.org/questions/new/firefox/form). The leading space must be preserved.
                field.label_suffix = _lazy(" (optional):")

        for name, field in self.fields.items():
            if field.help_text:
                bound = self[name]
                bound.help_id = f"{bound.id_for_label}_help"
                if field.widget.attrs.get("aria-describedby"):
                    field.widget.attrs["aria-describedby"] += " " + bound.help_id
                else:
                    field.widget.attrs["aria-describedby"] = bound.help_id

    def clean_content(self):
        """Validate that content field contains actual text, not just HTML markup."""
        content = self.cleaned_data.get("content", "")
        text_only = strip_tags(content)
        text_only = html.unescape(text_only).strip()

        if len(text_only) < 5:
            # L10n: An error message displayed under the "How can we help?" field when filing a question form if the submitted value contains too few non-HTML symbols.
            raise forms.ValidationError(_("Question content cannot be empty."))
        return content

    @property
    def metadata_field_keys(self):
        """Returns the keys of the metadata fields for the current
        form instance"""
        non_metadata_fields = ["title", "content", "email", "notifications", "category"]

        def metadata_filter(x):
            return x not in non_metadata_fields

        return list(filter(metadata_filter, list(self.fields.keys())))

    @property
    def cleaned_metadata(self):
        """Returns a dict with cleaned metadata values.  Omits
        fields with empty string value."""
        clean = {}
        for key in self.metadata_field_keys:
            if key in self.data and self.data[key] != "":
                clean[key] = self.cleaned_data[key]

        # Clean up the troubleshooting data if we have it.
        troubleshooting = clean.get("troubleshooting")
        if troubleshooting:
            try:
                parsed = json.loads(troubleshooting)
            except ValueError:
                parsed = None

            if parsed:
                # Clean out unwanted garbage preferences.
                if "modifiedPreferences" in parsed and isinstance(
                    parsed["modifiedPreferences"], dict
                ):
                    for pref in list(parsed["modifiedPreferences"].keys()):
                        if pref.startswith("print.macosx.pagesetup"):
                            del parsed["modifiedPreferences"][pref]

                # Remove any known PII from the troubleshooting data.
                remove_pii(parsed)

                clean["troubleshooting"] = json.dumps(parsed)

                # Override ff_version with the version in troubleshooting
                # which is more precise for the dot releases.
                version = parsed.get("application", {}).get("version")
                if version:
                    clean["ff_version"] = version

        return clean


class NewQuestionForm(EditQuestionForm):
    """Form to start a new question"""

    category = forms.ModelChoiceField(
        label=CATEGORY_LABEL,
        queryset=Topic.objects.none(),
        # L10n: A default option for dropdown menus (displayed when none of the actual options is selected).
        empty_label=_lazy("Please select..."),
        required=True,
    )

    # Collect user agent only when making a question for the first time.
    # Otherwise, we could grab moderators' user agents.
    useragent = forms.CharField(widget=forms.HiddenInput(), required=False)

    notifications = forms.BooleanField(label=NOTIFICATIONS_LABEL, initial=True, required=False)

    field_order = ["title", "category", "content"]

    def __init__(self, product=None, *args, **kwargs):
        """Add fields particular to new questions."""
        super().__init__(product=product, *args, **kwargs)

        if product:
            topics = Topic.active.filter(products=product, in_aaq=True)
            self.fields["category"].queryset = topics

    def save(self, user, locale, product, *args, **kwargs):
        self.instance.creator = user
        self.instance.locale = locale
        self.instance.product = product

        category = self.cleaned_data["category"]
        if category:
            self.instance.topic = category

        question = super().save(*args, **kwargs)

        if self.cleaned_data.get("notifications", False):
            QuestionReplyEvent.notify(question.creator, question)

        user_ct = ContentType.objects.get_for_model(user)
        qst_ct = ContentType.objects.get_for_model(question)
        # Move over to the question all of the images I added to the reply form
        up_images = ImageAttachment.objects.filter(creator=user, content_type=user_ct)
        up_images.update(content_type=qst_ct, object_id=question.id)

        # User successfully submitted a new question
        question.add_metadata(**self.cleaned_metadata)

        # The first time a question is saved, automatically apply some tags:
        question.auto_tag()

        return question


class AnswerForm(KitsuneBaseForumForm):
    """Form for replying to a question."""

    content = forms.CharField(
        label=_lazy("Content:"),
        min_length=5,
        max_length=10000,
        widget=forms.Textarea(attrs={"placeholder": REPLY_PLACEHOLDER}),
    )

    class Meta:
        model = Answer
        fields = ("content",)

    def clean(self, *args, **kwargs):
        """Override clean method to exempt question owner from spam filtering."""
        cdata = super().clean(*args, **kwargs)
        # if there is a reply from the owner, remove the spam flag
        if self.user and self.question and self.user == self.question.creator:
            cdata.pop("is_spam", None)

        return cdata


class WatchQuestionForm(forms.Form):
    """Form to subscribe to question updates."""

    EVENT_TYPE_CHOICES = (
        ("reply", "when anybody replies."),
        ("solution", "when a solution is found."),
    )

    email = forms.EmailField(
        required=False, widget=forms.TextInput(attrs={"placeholder": EMAIL_PLACEHOLDER})
    )
    event_type = forms.ChoiceField(choices=EVENT_TYPE_CHOICES, widget=forms.RadioSelect)

    def __init__(self, user, *args, **kwargs):
        # Initialize with logged in user's email.
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_email(self):
        if not self.user.is_authenticated and not self.cleaned_data["email"]:
            raise forms.ValidationError(_("Please provide an email."))
        elif not self.user.is_authenticated:
            return self.cleaned_data["email"]
        # Clear out the email for logged in users, we don't want to use it.
        return None
