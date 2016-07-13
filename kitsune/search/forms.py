import time

from django import forms
from django.conf import settings
from django.utils.translation import ugettext_lazy as _lazy

from kitsune import search as constants
from kitsune.forums.models import Forum as DiscussionForum
from kitsune.lib.sumo_locales import LOCALES
from kitsune.products.models import Product, Topic
from kitsune.sumo.form_fields import TypedMultipleChoiceField
from kitsune.wiki.config import CATEGORIES


MAX_QUERY_LENGTH = 200
SEARCH_LANGUAGES = [(k, LOCALES[k].native) for
                    k in settings.SUMO_LANGUAGES]


class SimpleSearchForm(forms.Form):
    """Django form to handle the simple search case."""
    q = forms.CharField(required=True, max_length=MAX_QUERY_LENGTH)

    w = forms.TypedChoiceField(required=False, coerce=int,
                               widget=forms.HiddenInput,
                               empty_value=constants.WHERE_BASIC,
                               choices=((constants.WHERE_SUPPORT, None),
                                        (constants.WHERE_WIKI, None),
                                        (constants.WHERE_BASIC, None),
                                        (constants.WHERE_DISCUSSION, None)))

    explain = forms.BooleanField(required=False)
    all_products = forms.BooleanField(required=False)
    language = forms.CharField(required=False)

    product = forms.MultipleChoiceField(
        required=False,
        label=_lazy(u'Relevant to'),
        widget=forms.CheckboxSelectMultiple())

    def __init__(self, *args, **kwargs):
        super(SimpleSearchForm, self).__init__(*args, **kwargs)

        product_field = self.fields['product']
        product_field.choices = Product.objects.values_list('slug', 'title')

    def clean_products(self):
        products = self.cleaned_data['products']
        # If products were specified or all_products was set, then we return
        # the products as is.
        if products or self.cleaned_data['all_products']:
            return products

        # If no products were specified and we're not looking for all_products,
        # then populate products by looking at things in the query.
        lowered_q = self.cleaned_data['q'].lower()

        if 'thunderbird' in lowered_q:
            products.append('thunderbird')
        elif 'android' in lowered_q:
            products.append('mobile')
        elif ('ios' in lowered_q or 'ipad' in lowered_q or 'ipod' in lowered_q or
              'iphone' in lowered_q):
            products.append('ios')
        elif 'firefox os' in lowered_q:
            products.append('firefox-os')
        elif 'firefox' in lowered_q:
            products.append('firefox')
        return products


class AdvancedSearchForm(forms.Form):
    """Django form for handling display and validation"""
    # Common fields
    q = forms.CharField(required=False, max_length=MAX_QUERY_LENGTH)

    w = forms.TypedChoiceField(required=False, coerce=int,
                               widget=forms.HiddenInput,
                               empty_value=constants.WHERE_BASIC,
                               choices=((constants.WHERE_SUPPORT, None),
                                        (constants.WHERE_WIKI, None),
                                        (constants.WHERE_BASIC, None),
                                        (constants.WHERE_DISCUSSION, None)))

    # TODO: get rid of this.
    a = forms.IntegerField(required=False, widget=forms.HiddenInput)

    # KB fields
    topics = forms.MultipleChoiceField(
        required=False,
        widget=forms.CheckboxSelectMultiple(),
        label=_lazy(u'Topics'))

    language = forms.ChoiceField(required=False, label=_lazy(u'Language'),
                                 choices=SEARCH_LANGUAGES)

    category = TypedMultipleChoiceField(
        required=False, coerce=int, widget=forms.CheckboxSelectMultiple,
        label=_lazy(u'Category'), choices=CATEGORIES, coerce_only=True)

    product = forms.MultipleChoiceField(
        required=False,
        label=_lazy(u'Relevant to'),
        widget=forms.CheckboxSelectMultiple())

    include_archived = forms.BooleanField(
        required=False, label=_lazy(u'Include obsolete articles?'))

    sortby_documents = forms.TypedChoiceField(
        required=False,
        empty_value=constants.SORTBY_DOCUMENTS_CHOICES[0][0],
        label=_lazy(u'Sort results by'),
        choices=constants.SORTBY_DOCUMENTS_CHOICES)

    # Support questions and discussion forums fields
    created = forms.TypedChoiceField(
        required=False, coerce=int, empty_value=0,
        label=_lazy(u'Created'), choices=constants.DATE_LIST)

    created_date = forms.CharField(required=False)

    updated = forms.TypedChoiceField(
        required=False, coerce=int, empty_value=0,
        label=_lazy(u'Last updated'), choices=constants.DATE_LIST)
    updated_date = forms.CharField(required=False)

    user_widget = forms.TextInput(attrs={'placeholder': _lazy(u'username'),
                                         'class': 'auto-fill'})
    # Discussion forums fields
    author = forms.CharField(required=False, widget=user_widget)

    sortby = forms.TypedChoiceField(
        required=False, coerce=int, empty_value=0,
        label=_lazy(u'Sort results by'), choices=constants.SORTBY_FORUMS)

    thread_type = TypedMultipleChoiceField(
        required=False, coerce=int, widget=forms.CheckboxSelectMultiple,
        label=_lazy(u'Thread type'), choices=constants.DISCUSSION_STATUS_LIST,
        coerce_only=True)

    forum = TypedMultipleChoiceField(
        required=False,
        coerce=int,
        label=_lazy(u'Search in forum'),
        choices=[],  # Note: set choices with set_allowed_forums
        coerce_only=True)

    # Support questions fields
    asked_by = forms.CharField(required=False, widget=user_widget)
    answered_by = forms.CharField(required=False, widget=user_widget)

    sortby_questions = forms.TypedChoiceField(
        required=False, coerce=int, empty_value=0,
        label=_lazy(u'Sort results by'), choices=constants.SORTBY_QUESTIONS)

    is_locked = forms.TypedChoiceField(
        required=False, coerce=int, empty_value=0, widget=forms.RadioSelect,
        label=_lazy(u'Locked'), choices=constants.TERNARY_LIST)

    is_archived = forms.TypedChoiceField(
        required=False, coerce=int, empty_value=0, widget=forms.RadioSelect,
        label=_lazy(u'Archived'), choices=constants.TERNARY_LIST)

    is_solved = forms.TypedChoiceField(
        required=False, coerce=int, empty_value=0, widget=forms.RadioSelect,
        label=_lazy(u'Solved'), choices=constants.TERNARY_LIST)

    has_answers = forms.TypedChoiceField(
        required=False, coerce=int, empty_value=0, widget=forms.RadioSelect,
        label=_lazy(u'Has answers'), choices=constants.TERNARY_LIST)

    has_helpful = forms.TypedChoiceField(
        required=False, coerce=int, empty_value=0, widget=forms.RadioSelect,
        label=_lazy(u'Has helpful answers'), choices=constants.TERNARY_LIST)

    num_voted = forms.TypedChoiceField(
        required=False, coerce=int, empty_value=0,
        label=_lazy(u'Votes'), choices=constants.NUMBER_LIST)
    num_votes = forms.IntegerField(required=False)

    tag_widget = forms.TextInput(attrs={'placeholder': _lazy(u'tag1, tag2'),
                                        'class': 'auto-fill'})
    q_tags = forms.CharField(label=_lazy(u'Tags'), required=False,
                             widget=tag_widget)

    def __init__(self, *args, **kwargs):
        super(AdvancedSearchForm, self).__init__(*args, **kwargs)

        product_field = self.fields['product']
        product_field.choices = Product.objects.values_list('slug', 'title')

        topics_field = self.fields['topics']
        topics_field.choices = Topic.objects.values_list(
            'slug', 'title').distinct()

    def clean(self):
        """Clean up data and set defaults"""
        c = self.cleaned_data

        # Validate created and updated dates
        date_fields = (('created', 'created_date'),
                       ('updated', 'updated_date'))
        for field_option, field_date in date_fields:
            if c[field_date] != '':
                try:
                    created_timestamp = time.mktime(
                        time.strptime(c[field_date], '%m/%d/%Y'))
                    c[field_date] = int(created_timestamp)
                except (ValueError, OverflowError):
                    c[field_option] = None
            else:
                c[field_option] = None

        # Empty value defaults to int
        c['num_votes'] = c.get('num_votes') or 0
        return c

    def clean_category(self):
        category = self.cleaned_data['category']
        if not category:
            category = settings.SEARCH_DEFAULT_CATEGORIES
        return category

    def set_allowed_forums(self, user):
        """Sets the 'forum' field choices to forums the user can see."""
        forums = [(f.id, f.name)
                  for f in DiscussionForum.authorized_forums_for_user(user)]
        self.fields['forum'].choices = forums
