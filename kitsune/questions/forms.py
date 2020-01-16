import json
from datetime import date, timedelta

from django import forms
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import ugettext as _
from django.utils.translation import ugettext_lazy as _lazy

from kitsune.products.models import Topic
from kitsune.questions.events import QuestionReplyEvent
from kitsune.questions.models import Answer, Question
from kitsune.upload.models import ImageAttachment

# labels and help text
SITE_AFFECTED_LABEL = _lazy(u"URL of affected site")
CRASH_ID_LABEL = _lazy(u"Crash ID(s)")
CRASH_ID_HELP = _lazy(
    u"If you submit information to Mozilla when you crash, "
    u"you'll be given a crash ID which uniquely identifies "
    u"your crash and lets us look at details that may help "
    u"identify the cause. To find your recently submitted "
    u"crash IDs, go to <strong>about:crashes</strong> in "
    u"your location bar. <a href='https://support.mozilla."
    u"com/en-US/kb/Firefox+crashes#Getting_the_most_"
    u"accurate_help_with_your_Firefox_crash' "
    u"target='_blank'>Click for detailed instructions</a>."
)
TROUBLESHOOTING_LABEL = _lazy(u"Troubleshooting Information")
TROUBLESHOOTING_HELP = _lazy(
    u"This information gives details about the "
    u"internal workings of your browser that will "
    u"help in answering your question."
)
FREQUENCY_LABEL = _lazy(u"This happens")
FREQUENCY_CHOICES = [
    (u"", u""),
    (u"NOT_SURE", _lazy(u"Not sure how often")),
    (u"ONCE_OR_TWICE", _lazy(u"Just once or twice")),
    (u"FEW_TIMES_WEEK", _lazy(u"A few times a week")),
    (u"EVERY_TIME", _lazy(u"Every time Firefox opened")),
]
STARTED_LABEL = _lazy(u"This started when...")
TITLE_LABEL = _lazy(u"Subject")
CONTENT_LABEL = _lazy(u"How can we help?")
FF_VERSION_LABEL = _lazy(u"Firefox version")
OS_LABEL = _lazy(u"Operating system")
PLUGINS_LABEL = _lazy(u"Installed plugins")
ADDON_LABEL = _lazy(u"Extension/plugin you are having trouble with")
DEVICE_LABEL = _lazy(u"Mobile device")
CATEGORY_LABEL = _lazy(u"Which topic best describes your question?")
NOTIFICATIONS_LABEL = _lazy(u"Email me when someone answers the thread")

REPLY_PLACEHOLDER = _lazy(u"Enter your reply here.")
EMAIL_PLACEHOLDER = _lazy(u"Enter your email address here.")


class EditQuestionForm(forms.ModelForm):
    """Form to edit an existing question"""

    title = forms.CharField(
        label=TITLE_LABEL,
        min_length=5
    )

    content = forms.CharField(
        label=CONTENT_LABEL,
        min_length=5,
        widget=forms.Textarea()
    )

    class Meta:
        model = Question
        fields = [
            'title',
            'content',
        ]

    def __init__(self, product=None, *args, **kwargs):
        """Init the form.

        We are adding fields here and not declaratively because the
        form fields to include depend on the selected product/category.
        """
        super(EditQuestionForm, self).__init__(*args, **kwargs)

        #  Extra fields required by product/category selected
        extra_fields = []

        if product:
            extra_fields += product.get("extra_fields", [])

        if "sites_affected" in extra_fields:
            field = forms.CharField(
                label=SITE_AFFECTED_LABEL,
                initial="http://",
                required=False,
                max_length=255,
                widget=forms.TextInput(),
            )
            self.fields["sites_affected"] = field

        if "crash_id" in extra_fields:
            field = forms.CharField(
                label=CRASH_ID_LABEL,
                help_text=CRASH_ID_HELP,
                required=False,
                max_length=255,
                widget=forms.TextInput(),
            )
            self.fields["crash_id"] = field

        if "frequency" in extra_fields:
            field = forms.ChoiceField(
                label=FREQUENCY_LABEL, choices=FREQUENCY_CHOICES, required=False
            )
            self.fields["frequency"] = field

        if "started" in extra_fields:
            field = forms.CharField(
                label=STARTED_LABEL,
                required=False,
                max_length=255,
                widget=forms.TextInput(),
            )
            self.fields["started"] = field

        if "addon" in extra_fields:
            field = forms.CharField(
                label=ADDON_LABEL,
                required=False,
                max_length=255,
                widget=forms.TextInput(),
            )
            self.fields["addon"] = field

        if "ff_version" in extra_fields:
            self.fields["ff_version"] = forms.CharField(
                label=FF_VERSION_LABEL, required=False,
            )

        if "device" in extra_fields:
            self.fields["device"] = forms.CharField(label=DEVICE_LABEL, required=False,)

        if "os" in extra_fields:
            self.fields["os"] = forms.CharField(label=OS_LABEL, required=False,)

        if "plugins" in extra_fields:
            widget = forms.Textarea(attrs={"class": "plugins"})
            self.fields["plugins"] = forms.CharField(
                label=PLUGINS_LABEL, required=False, widget=widget,
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
                field.label_suffix = _lazy(" (optional):")

    @property
    def metadata_field_keys(self):
        """Returns the keys of the metadata fields for the current
        form instance"""
        non_metadata_fields = ["title", "content", "email", "notifications"]

        def metadata_filter(x):
            return x not in non_metadata_fields

        return list(filter(metadata_filter, list(self.fields.keys())))

    @property
    def cleaned_metadata(self):
        """Returns a dict with cleaned metadata values.  Omits
        fields with empty string value."""
        clean = {}
        for key in self.metadata_field_keys:
            if key in self.data and self.data[key] != u"":
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
                if ('modifiedPreferences' in parsed and
                        isinstance(parsed['modifiedPreferences'], dict)):
                    for pref in list(parsed['modifiedPreferences'].keys()):
                        if pref.startswith('print.macosx.pagesetup'):
                            del parsed['modifiedPreferences'][pref]
                    clean['troubleshooting'] = json.dumps(parsed)

                # Override ff_version with the version in troubleshooting
                # which is more precise for the dot releases.
                version = parsed.get("application", {}).get("version")
                if version:
                    clean["ff_version"] = version

        return clean


class NewQuestionForm(EditQuestionForm):
    """Form to start a new question"""

    category = forms.ChoiceField(
        label=CATEGORY_LABEL,
        choices=[],
    )

    # Collect user agent only when making a question for the first time.
    # Otherwise, we could grab moderators' user agents.
    useragent = forms.CharField(
        widget=forms.HiddenInput(), required=False
    )

    notifications = forms.BooleanField(
        label=NOTIFICATIONS_LABEL,
        initial=True,
        required=False
    )

    field_order = [
        'title',
        'category',
        'content'
    ]

    def __init__(self, product=None, *args, **kwargs):
        """Add fields particular to new questions."""
        super(NewQuestionForm, self).__init__(
            product=product, *args, **kwargs
        )

        if product:
            category_choices = [
                (key, value["name"]) for key, value in product["categories"].items()
            ]
            category_choices.insert(0, ("", "Please select"))
            self.fields["category"].choices = category_choices

    def save(self, user, locale, product, product_config, *args, **kwargs):
        self.instance.creator = user
        self.instance.locale = locale
        self.instance.product = product

        category_config = product_config['categories'][self.cleaned_data['category']]
        if category_config:
            t = category_config.get("topic")
            if t:
                self.instance.topic = Topic.objects.get(slug=t, product=product)

        question = super(NewQuestionForm, self).save(*args, **kwargs)

        if self.cleaned_data.get('notifications', False):
            QuestionReplyEvent.notify(question.creator, question)

        user_ct = ContentType.objects.get_for_model(user)
        qst_ct = ContentType.objects.get_for_model(question)
        # Move over to the question all of the images I added to the reply form
        up_images = ImageAttachment.objects.filter(
            creator=user, content_type=user_ct
        )
        up_images.update(content_type=qst_ct, object_id=question.id)

        # User successfully submitted a new question
        question.add_metadata(**self.cleaned_metadata)

        if product_config:
            # TODO: This add_metadata call should be removed once we are
            # fully IA-driven (sync isn't special case anymore).
            question.add_metadata(product=product_config["key"])

        # The first time a question is saved, automatically apply some tags:
        question.auto_tag()

        return question


class AnswerForm(forms.Form):
    """Form for replying to a question."""

    content = forms.CharField(
        label=_lazy("Content:"),
        min_length=5,
        max_length=10000,
        widget=forms.Textarea(attrs={"placeholder": REPLY_PLACEHOLDER})
    )

    class Meta:
        model = Answer
        fields = ("content",)


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
        super(WatchQuestionForm, self).__init__(*args, **kwargs)

    def clean_email(self):
        if not self.user.is_authenticated() and not self.cleaned_data["email"]:
            raise forms.ValidationError(_("Please provide an email."))
        elif not self.user.is_authenticated():
            return self.cleaned_data["email"]
        # Clear out the email for logged in users, we don't want to use it.
        return None


bucket_choices = [(1, "1 day"), (7, "1 week"), (30, "1 month")]


class StatsForm(forms.Form):
    bucket = forms.IntegerField(
        min_value=1,
        required=False,
        label=_lazy(u"Interval"),
        widget=forms.Select(choices=bucket_choices),
    )
    start = forms.DateField(required=False, label=_lazy(u"Start"))
    end = forms.DateField(required=False, label=_lazy(u"End"))

    def clean_bucket(self):
        if self.cleaned_data.get("bucket") is None:
            return 1
        return self.cleaned_data["bucket"]

    def clean_start(self):
        if self.cleaned_data.get("start") is None:
            return date.today() - timedelta(days=30)
        return self.cleaned_data["start"]

    def clean_end(self):
        if self.cleaned_data.get("end") is None:
            return date.today()
        return self.cleaned_data["end"]

    def clean(self):
        start = self.cleaned_data.get("start")
        end = self.cleaned_data.get("end")
        if start and end and start > end:
            raise forms.ValidationError("Start must be less than end.")
        return self.cleaned_data
