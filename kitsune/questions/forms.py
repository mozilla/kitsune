import json
from datetime import date, timedelta

from django import forms
from django.utils.translation import ugettext_lazy as _lazy, ugettext as _

from kitsune.questions.marketplace import submit_ticket
from kitsune.questions.models import Answer

# labels and help text
SITE_AFFECTED_LABEL = _lazy('URL of affected site')
CRASH_ID_LABEL = _lazy('Crash ID(s)')
CRASH_ID_HELP = _lazy("If you submit information to Mozilla when you crash, "
                      "you'll be given a crash ID which uniquely identifies "
                      "your crash and lets us look at details that may help "
                      "identify the cause. To find your recently submitted "
                      "crash IDs, go to <strong>about:crashes</strong> in "
                      "your location bar. <a href='https://support.mozilla."
                      "com/en-US/kb/Firefox+crashes#Getting_the_most_"
                      "accurate_help_with_your_Firefox_crash' "
                      "target='_blank'>Click for detailed instructions</a>.")
TROUBLESHOOTING_LABEL = _lazy('Troubleshooting Information')
TROUBLESHOOTING_HELP = _lazy('This information gives details about the '
                             'internal workings of your browser that will '
                             'help in answering your question.')
FREQUENCY_LABEL = _lazy('This happens')
FREQUENCY_CHOICES = [('', ''),
                     ('NOT_SURE', _lazy('Not sure how often')),
                     ('ONCE_OR_TWICE', _lazy('Just once or twice')),
                     ('FEW_TIMES_WEEK', _lazy('A few times a week')),
                     ('EVERY_TIME', _lazy('Every time Firefox opened')), ]
STARTED_LABEL = _lazy('This started when...')
TITLE_LABEL = _lazy('Question')
CONTENT_LABEL = _lazy('Details')
EMAIL_LABEL = _lazy('Email')
EMAIL_HELP = _lazy('A confirmation email will be sent to this address in '
                   'order to post your question.')
FF_VERSION_LABEL = _lazy('Firefox version')
OS_LABEL = _lazy('Operating system')
PLUGINS_LABEL = _lazy('Installed plugins')
ADDON_LABEL = _lazy('Extension/plugin you are having trouble with')
DEVICE_LABEL = _lazy('Mobile device')

# Validation error messages
MSG_TITLE_REQUIRED = _lazy('Please provide a question.')
MSG_TITLE_SHORT = _lazy('Your question is too short (%(show_value)s '
                        'characters). It must be at least %(limit_value)s '
                        'characters.')
MSG_TITLE_LONG = _lazy('Please keep the length of your question to '
                       '%(limit_value)s characters or less. It is currently '
                       '%(show_value)s characters.')
MSG_CONTENT_REQUIRED = _lazy('Please provide content.')
MSG_CONTENT_SHORT = _lazy('Your content is too short (%(show_value)s '
                          'characters). It must be at least %(limit_value)s '
                          'characters.')
MSG_CONTENT_LONG = _lazy('Please keep the length of your content to '
                         '%(limit_value)s characters or less. It is '
                         'currently %(show_value)s characters.')

REPLY_PLACEHOLDER = _lazy('Enter your reply here.')

# Marketplace AAQ form
EMAIL_PLACEHOLDER = _lazy('Enter your email address here.')
SUBJECT_PLACEHOLDER = _lazy('Enter a subject here.')
SUBJECT_CONTENT_REQUIRED = _lazy('Please provide a subject.')
SUBJECT_CONTENT_SHORT = _lazy(
    'The subject is too short (%(show_value)s '
    'characters). It must be at least %(limit_value)s '
    'characters.')
SUBJECT_CONTENT_LONG = _lazy('Please keep the length of the subject to '
                             '%(limit_value)s characters or less. It is '
                             'currently %(show_value)s characters.')
BODY_PLACEHOLDER = _lazy('Describe your issue here.')
BODY_CONTENT_REQUIRED = _lazy('Please describe your issue in the body.')
BODY_CONTENT_SHORT = _lazy('The body content is too short (%(show_value)s '
                           'characters). It must be at least %(limit_value)s '
                           'characters.')
BODY_CONTENT_LONG = _lazy('Please keep the length of the body content to '
                          '%(limit_value)s characters or less. It is '
                          'currently %(show_value)s characters.')
CATEGORY_CHOICES = [('account', _lazy('Account Issues')),
                    ('installation', _lazy('Installation Issues')),
                    ('payment', _lazy('Payment Issues')),
                    ('application', _lazy('Application Issues')), ]

# Marketplace Request Refund form
TRANSACTION_ID_PLACEHOLDER = _lazy('Enter the Transaction ID here.')
TRANSACTION_ID_REQUIRED = _lazy('Please provide the Transaction ID.')
REFUND_CATEGORY_CHOICES = [
    ('Defective', _lazy('Defective')),
    ('Malware', _lazy('Malware')),
    ('Did not work as expected', _lazy('Did not work as expected')),
    ('Seller will not provide support',
     _lazy('Seller will not provide support')), ]


# Marketplace Developer Request form
DEVELOPER_REQUEST_CATEGORY_CHOICES = [
    ('Account Administration', _lazy('Account Administration')),
    ('Review Process', _lazy('Review Process')),
    ('Payments/Settlement', _lazy('Payments/Settlement')), ]


class EditQuestionForm(forms.Form):
    """Form to edit an existing question"""

    def __init__(self, product=None, category=None, *args,
                 **kwargs):
        """Init the form.

        We are adding fields here and not declaratively because the
        form fields to include depend on the selected product/category.
        """
        super(EditQuestionForm, self).__init__(*args, **kwargs)

        #  Extra fields required by product/category selected
        extra_fields = []

        if product:
            extra_fields += product.get('extra_fields', [])
        if category:
            extra_fields += category.get('extra_fields', [])

        #  Add the fields to the form
        error_messages = {'required': MSG_TITLE_REQUIRED,
                          'min_length': MSG_TITLE_SHORT,
                          'max_length': MSG_TITLE_LONG}
        field = forms.CharField(
            label=TITLE_LABEL, min_length=5, max_length=160, widget=forms.TextInput(),
            error_messages=error_messages)
        self.fields['title'] = field

        error_messages = {'required': MSG_CONTENT_REQUIRED,
                          'min_length': MSG_CONTENT_SHORT,
                          'max_length': MSG_CONTENT_LONG}
        field = forms.CharField(
            label=CONTENT_LABEL, min_length=5, max_length=10000, widget=forms.Textarea(),
            error_messages=error_messages)
        self.fields['content'] = field

        if 'sites_affected' in extra_fields:
            field = forms.CharField(
                label=SITE_AFFECTED_LABEL,
                initial='http://',
                required=False,
                max_length=255,
                widget=forms.TextInput(),
            )
            self.fields['sites_affected'] = field

        if 'crash_id' in extra_fields:
            field = forms.CharField(
                label=CRASH_ID_LABEL,
                help_text=CRASH_ID_HELP,
                required=False,
                max_length=255,
                widget=forms.TextInput(),
            )
            self.fields['crash_id'] = field

        if 'frequency' in extra_fields:
            field = forms.ChoiceField(label=FREQUENCY_LABEL,
                                      choices=FREQUENCY_CHOICES,
                                      required=False)
            self.fields['frequency'] = field

        if 'started' in extra_fields:
            field = forms.CharField(
                label=STARTED_LABEL,
                required=False,
                max_length=255,
                widget=forms.TextInput(),
            )
            self.fields['started'] = field

        if 'addon' in extra_fields:
            field = forms.CharField(
                label=ADDON_LABEL,
                required=False,
                max_length=255,
                widget=forms.TextInput(),
            )
            self.fields['addon'] = field

        if 'troubleshooting' in extra_fields:
            widget = forms.Textarea(attrs={'class': 'troubleshooting'})
            field = forms.CharField(
                label=TROUBLESHOOTING_LABEL,
                help_text=TROUBLESHOOTING_HELP,
                required=False,
                max_length=655360,
                widget=widget,
            )
            self.fields['troubleshooting'] = field

        if 'ff_version' in extra_fields:
            self.fields['ff_version'] = forms.CharField(
                label=FF_VERSION_LABEL,
                required=False,
            )

        if 'device' in extra_fields:
            self.fields['device'] = forms.CharField(
                label=DEVICE_LABEL,
                required=False,
            )

        if 'os' in extra_fields:
            self.fields['os'] = forms.CharField(
                label=OS_LABEL,
                required=False,
            )

        if 'plugins' in extra_fields:
            widget = forms.Textarea(attrs={'class': 'plugins'})
            self.fields['plugins'] = forms.CharField(
                label=PLUGINS_LABEL,
                required=False,
                widget=widget,
            )

    @property
    def metadata_field_keys(self):
        """Returns the keys of the metadata fields for the current
        form instance"""
        non_metadata_fields = ['title', 'content', 'email']

        def metadata_filter(x):
            return x not in non_metadata_fields

        return list(filter(metadata_filter, list(self.fields.keys())))

    @property
    def cleaned_metadata(self):
        """Returns a dict with cleaned metadata values.  Omits
        fields with empty string value."""
        clean = {}
        for key in self.metadata_field_keys:
            if key in self.data and self.data[key] != '':
                clean[key] = self.cleaned_data[key]

        # Clean up the troubleshooting data if we have it.
        troubleshooting = clean.get('troubleshooting')
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
                version = parsed.get('application', {}).get('version')
                if version:
                    clean['ff_version'] = version

        return clean


class NewQuestionForm(EditQuestionForm):
    """Form to start a new question"""

    def __init__(self, product=None, category=None, *args,
                 **kwargs):
        """Add fields particular to new questions."""
        super(NewQuestionForm, self).__init__(product=product,
                                              category=category,
                                              *args, **kwargs)

        # Collect user agent only when making a question for the first time.
        # Otherwise, we could grab moderators' user agents.
        self.fields['useragent'] = forms.CharField(widget=forms.HiddenInput(),
                                                   required=False)


class AnswerForm(forms.Form):
    """Form for replying to a question."""
    content = forms.CharField(
        label=_lazy('Content:'),
        min_length=5,
        max_length=10000,
        widget=forms.Textarea(attrs={'placeholder': REPLY_PLACEHOLDER}),
        error_messages={'required': MSG_CONTENT_REQUIRED,
                        'min_length': MSG_CONTENT_SHORT,
                        'max_length': MSG_CONTENT_LONG})

    class Meta:
        model = Answer
        fields = ('content',)


class WatchQuestionForm(forms.Form):
    """Form to subscribe to question updates."""
    EVENT_TYPE_CHOICES = (
        ('reply', 'when anybody replies.'),
        ('solution', 'when a solution is found.'),
    )

    email = forms.EmailField(
        required=False,
        widget=forms.TextInput(attrs={'placeholder': EMAIL_PLACEHOLDER}))
    event_type = forms.ChoiceField(choices=EVENT_TYPE_CHOICES,
                                   widget=forms.RadioSelect)

    def __init__(self, user, *args, **kwargs):
        # Initialize with logged in user's email.
        self.user = user
        super(WatchQuestionForm, self).__init__(*args, **kwargs)

    def clean_email(self):
        if not self.user.is_authenticated() and not self.cleaned_data['email']:
            raise forms.ValidationError(_('Please provide an email.'))
        elif not self.user.is_authenticated():
            return self.cleaned_data['email']
        # Clear out the email for logged in users, we don't want to use it.
        return None


class BaseZendeskForm(forms.Form):
    """Base Form class for all Zendesk forms."""

    def __init__(self, user, *args, **kwargs):
        super(BaseZendeskForm, self).__init__(*args, **kwargs)

        self.user = user

        # Add email field for users not logged in.
        if not user.is_authenticated():
            email = forms.EmailField(
                label=_lazy('Email:'),
                widget=forms.TextInput(attrs={
                    'placeholder': EMAIL_PLACEHOLDER
                }))
            self.fields['email'] = email

    subject = forms.CharField(
        label=_lazy('Subject:'),
        min_length=4,
        max_length=255,
        widget=forms.TextInput(attrs={'placeholder': SUBJECT_PLACEHOLDER}),
        error_messages={'required': SUBJECT_CONTENT_REQUIRED,
                        'min_length': SUBJECT_CONTENT_SHORT,
                        'max_length': SUBJECT_CONTENT_LONG})

    body = forms.CharField(
        label=_lazy('Body:'),
        min_length=5,
        max_length=10000,
        widget=forms.Textarea(attrs={'placeholder': BODY_PLACEHOLDER}),
        error_messages={'required': BODY_CONTENT_REQUIRED,
                        'min_length': BODY_CONTENT_SHORT,
                        'max_length': BODY_CONTENT_LONG})

    def ticket_body(self, email):
        """Body of the ticket to submit to Zendesk."""
        return 'Email: {email}\n{body}'.format(
            email=email,
            body=self.cleaned_data['body'])

    def submit_ticket(self):
        """Submit the ticket to Zendesk."""
        if self.user.is_authenticated():
            email = self.user.email
        else:
            email = self.cleaned_data['email']

        submit_ticket(
            email,
            self.cleaned_data['category'],
            self.cleaned_data['subject'],
            self.ticket_body(email),
            [])


class MarketplaceAaqForm(BaseZendeskForm):
    category = forms.ChoiceField(
        label=_lazy('Category:'),
        choices=CATEGORY_CHOICES)


class MarketplaceRefundForm(BaseZendeskForm):
    transaction_id = forms.CharField(
        label=_lazy('Transaction ID:'),
        widget=forms.TextInput(attrs={
            'placeholder': TRANSACTION_ID_PLACEHOLDER
        }),
        error_messages={'required': TRANSACTION_ID_REQUIRED})

    category = forms.ChoiceField(
        label=_lazy('Category:'),
        choices=REFUND_CATEGORY_CHOICES)

    def ticket_body(self, email):
        """Body of the ticket to submit to Zendesk."""
        return 'Email: {email}\nTransaction ID: {id}\nCategory: {category}\n{body}'.format(
            email=email,
            id=self.cleaned_data['transaction_id'],
            category=self.cleaned_data['category'],
            body=self.cleaned_data['body'])


class MarketplaceDeveloperRequestForm(BaseZendeskForm):
    category = forms.ChoiceField(
        label=_lazy('Category:'),
        choices=DEVELOPER_REQUEST_CATEGORY_CHOICES)

    def ticket_body(self, email):
        """Body of the ticket to submit to Zendesk."""
        return 'Email: {email}\nCategory: {category}\n{body}'.format(
            email=email,
            category=self.cleaned_data['category'],
            body=self.cleaned_data['body'])


bucket_choices = [(1, '1 day'), (7, '1 week'), (30, '1 month')]


class StatsForm(forms.Form):
    bucket = forms.IntegerField(
        min_value=1, required=False, label=_lazy('Interval'),
        widget=forms.Select(choices=bucket_choices))
    start = forms.DateField(required=False, label=_lazy('Start'))
    end = forms.DateField(required=False, label=_lazy('End'))

    def clean_bucket(self):
        if self.cleaned_data.get('bucket') is None:
            return 1
        return self.cleaned_data['bucket']

    def clean_start(self):
        if self.cleaned_data.get('start') is None:
            return date.today() - timedelta(days=30)
        return self.cleaned_data['start']

    def clean_end(self):
        if self.cleaned_data.get('end') is None:
            return date.today()
        return self.cleaned_data['end']

    def clean(self):
        start = self.cleaned_data.get('start')
        end = self.cleaned_data.get('end')
        if start and end and start > end:
            raise forms.ValidationError('Start must be less than end.')
        return self.cleaned_data
