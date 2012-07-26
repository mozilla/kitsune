import json
import re

from django import forms
from django.template.defaultfilters import slugify
from django.utils.encoding import smart_str
from django.utils.safestring import mark_safe

from tower import ugettext_lazy as _lazy

from sumo.form_fields import MultiUsernameField, StrippedCharField
from topics.models import Topic
from wiki.models import Document, Revision
from wiki.config import (SIGNIFICANCES_HELP, GROUPED_FIREFOX_VERSIONS,
                         SIGNIFICANCES, GROUPED_OPERATING_SYSTEMS, CATEGORIES,
                         PRODUCTS, PRODUCT_TAGS)


TITLE_REQUIRED = _lazy(u'Please provide a title.')
TITLE_SHORT = _lazy(u'The title is too short (%(show_value)s characters). '
                    u'It must be at least %(limit_value)s characters.')
TITLE_LONG = _lazy(u'Please keep the length of the title to %(limit_value)s '
                   u'characters or less. It is currently %(show_value)s '
                   u'characters.')
SLUG_REQUIRED = _lazy(u'Please provide a slug.')
SLUG_INVALID = _lazy(u'The slug provided is not valid.')
SLUG_SHORT = _lazy(u'The slug is too short (%(show_value)s characters). '
                   u'It must be at least %(limit_value)s characters.')
SLUG_LONG = _lazy(u'Please keep the length of the slug to %(limit_value)s '
                  u'characters or less. It is currently %(show_value)s '
                  u'characters.')
SUMMARY_REQUIRED = _lazy(u'Please provide a summary.')
SUMMARY_SHORT = _lazy(u'The summary is too short (%(show_value)s characters). '
                      u'It must be at least %(limit_value)s characters.')
SUMMARY_LONG = _lazy(u'Please keep the length of the summary to '
                     u'%(limit_value)s characters or less. It is currently '
                     u'%(show_value)s characters.')
CONTENT_REQUIRED = _lazy(u'Please provide content.')
CONTENT_SHORT = _lazy(u'The content is too short (%(show_value)s characters). '
                      u'It must be at least %(limit_value)s characters.')
CONTENT_LONG = _lazy(u'Please keep the length of the content to '
                     u'%(limit_value)s characters or less. It is currently '
                     u'%(show_value)s characters.')
COMMENT_LONG = _lazy(u'Please keep the length of the comment to '
                     u'%(limit_value)s characters or less. It is currently '
                     u'%(show_value)s characters.')


class DocumentForm(forms.ModelForm):
    """Form to create/edit a document."""
    def __init__(self, *args, **kwargs):
        # Quasi-kwargs:
        can_archive = kwargs.pop('can_archive', False)
        initial_title = kwargs.pop('initial_title', '')
        initial_comment = kwargs.pop('initial_comment', '')

        super(DocumentForm, self).__init__(*args, **kwargs)

        title_field = self.fields['title']
        title_field.initial = initial_title

        slug_field = self.fields['slug']
        slug_field.initial = slugify(initial_title)

        comment_field = self.fields['needs_change_comment']
        comment_field.initial = initial_comment

        topics_field = self.fields['topics']
        topics_field.choices = Topic.objects.values_list('id', 'title')

        # If user hasn't permission to frob is_archived, remove the field. This
        # causes save() to skip it as well.
        if not can_archive:
            del self.fields['is_archived']

    title = StrippedCharField(
        min_length=5, max_length=255,
        widget=forms.TextInput(),
        label=_lazy(u'Title:'),
        help_text=_lazy(u'Title of article'),
        error_messages={'required': TITLE_REQUIRED,
                        'min_length': TITLE_SHORT,
                        'max_length': TITLE_LONG})

    # We don't use forms.SlugField because it is too strict in
    # what it allows (English/Roman alpha-numeric characters and dashes).
    # Instead, we do custom validation in `clean_slug` below.
    slug = StrippedCharField(
        min_length=3, max_length=255,
        widget=forms.TextInput(),
        label=_lazy(u'Slug:'),
        help_text=_lazy(u'Article URL'),
        error_messages={'required': SLUG_REQUIRED,
                        'min_length': SLUG_SHORT,
                        'max_length': SLUG_LONG})

    product_tags = forms.MultipleChoiceField(
        label=_lazy(u'Relevant to:'),
        choices=PRODUCTS,
        initial=[PRODUCTS[0][0]],
        required=False,
        widget=forms.CheckboxSelectMultiple())

    is_localizable = forms.BooleanField(
        initial=True,
        label=_lazy(u'Allow translations:'),
        required=False)

    is_archived = forms.BooleanField(
        label=_lazy(u'Obsolete:'),
        required=False)

    allow_discussion = forms.BooleanField(
        label=_lazy(u'Allow discussion on this article?'),
        initial=True,
        required=False)

    category = forms.ChoiceField(
        choices=CATEGORIES,
        # Required for non-translations, which is
        # enforced in Document.clean().
        required=False,
        label=_lazy(u'Category:'),
        help_text=_lazy(u'Type of article'))

    topics = forms.MultipleChoiceField(
        label=_lazy(u'Topics:'),
        required=False,
        widget=forms.CheckboxSelectMultiple())

    locale = forms.CharField(widget=forms.HiddenInput())

    needs_change = forms.BooleanField(
        label=_lazy(u'Needs change:'),
        initial=False,
        required=False)

    needs_change_comment = forms.CharField(
        label=_lazy(u'Comment:'),
        widget=forms.Textarea(),
        required=False)

    def clean_slug(self):
        slug = self.cleaned_data['slug']
        # Blacklist /, ? and +
        if not re.compile(r'^[^/^\+^\?]+$').match(slug):
            raise forms.ValidationError(SLUG_INVALID)
        return slug

    class Meta:
        model = Document
        fields = ('title', 'slug', 'category', 'is_localizable', 'product_tags',
                  'topics', 'locale', 'is_archived', 'allow_discussion',
                  'needs_change', 'needs_change_comment')

    def save(self, parent_doc, **kwargs):
        """Persist the Document form, and return the saved Document."""
        doc = super(DocumentForm, self).save(commit=False, **kwargs)
        doc.parent = parent_doc

        # If document doesn't need change, clear out the comment.
        if not doc.needs_change:
            doc.needs_change_comment = ''

        doc.save()
        self.save_m2m()

        if not parent_doc:
            # Set the products as tags.
            # products are not set on the translations.
            prods = self.cleaned_data['product_tags']
            doc.tags.add(*prods)
            doc.tags.remove(*[p for p in PRODUCT_TAGS if p not in prods])

        return doc


class RevisionForm(forms.ModelForm):
    """Form to create new revisions."""
    keywords = StrippedCharField(required=False,
                                 label=_lazy(u'Keywords:'),
                                 help_text=_lazy(u'Affects search results'))

    summary = StrippedCharField(
                min_length=5, max_length=1000, widget=forms.Textarea(),
                label=_lazy(u'Search result summary:'),
                help_text=_lazy(u'Only displayed on search results page'),
                error_messages={'required': SUMMARY_REQUIRED,
                                'min_length': SUMMARY_SHORT,
                                'max_length': SUMMARY_LONG})

    showfor_data = {
        'oses': [(smart_str(c[0][0]), [(o.slug, smart_str(o.name)) for
                                    o in c[1]]) for
                 c in GROUPED_OPERATING_SYSTEMS],
        'versions': [(smart_str(c[0][0]), [(v.slug, smart_str(v.name)) for
                                        v in c[1] if v.show_in_ui]) for
                     c in GROUPED_FIREFOX_VERSIONS]}
    content = StrippedCharField(
                min_length=5, max_length=100000,
                label=_lazy(u'Content:'),
                widget=forms.Textarea(attrs={'data-showfor':
                                             json.dumps(showfor_data)}),
                error_messages={'required': CONTENT_REQUIRED,
                                'min_length': CONTENT_SHORT,
                                'max_length': CONTENT_LONG})

    comment = StrippedCharField(required=False, label=_lazy(u'Comment:'))

    class Meta(object):
        model = Revision
        fields = ('keywords', 'summary', 'content', 'comment', 'based_on')

    def __init__(self, *args, **kwargs):
        super(RevisionForm, self).__init__(*args, **kwargs)
        self.fields['based_on'].widget = forms.HiddenInput()

    def save(self, creator, document, **kwargs):
        """Persist me, and return the saved Revision.

        Take several other necessary pieces of data that aren't from the
        form.

        """
        # Throws a TypeError if somebody passes in a commit kwarg:
        new_rev = super(RevisionForm, self).save(commit=False, **kwargs)

        new_rev.document = document
        new_rev.creator = creator
        new_rev.save()
        return new_rev


class RadioInputWithHelpText(forms.widgets.RadioInput):
    """Extend django's RadioInput with some <div class="help-text" />."""
    # NOTE: I tried to have the help text be part of the choices tuple,
    # but it caused all sorts of validation errors in django. For now,
    # just using SIGNIFICANCES_HELP directly here.
    def __init__(self, name, value, attrs, choice, index):
        super(RadioInputWithHelpText, self).__init__(name, value, attrs,
                                                     choice, index)
        self.choice_help = SIGNIFICANCES_HELP[choice[0]]

    def __unicode__(self):
        label = super(RadioInputWithHelpText, self).__unicode__()
        return mark_safe('%s<div class="help-text">%s</div>' %
                         (label, self.choice_help))


class RadioFieldRendererWithHelpText(forms.widgets.RadioFieldRenderer):
    """Modifies django's RadioFieldRenderer to use RadioInputWithHelpText."""
    def __iter__(self):
        for i, choice in enumerate(self.choices):
            yield RadioInputWithHelpText(self.name, self.value,
                                         self.attrs.copy(), choice, i)


class ReviewForm(forms.Form):
    comment = StrippedCharField(max_length=2000, widget=forms.Textarea(),
                                required=False, label=_lazy(u'Comment:'),
                                error_messages={'max_length': COMMENT_LONG})

    _widget = forms.RadioSelect(renderer=RadioFieldRendererWithHelpText)
    significance = forms.ChoiceField(
                    label=_lazy(u'Significance:'),
                    choices=SIGNIFICANCES,
                    initial=SIGNIFICANCES[1][0],
                    required=False, widget=_widget)

    is_ready_for_localization = forms.BooleanField(
        initial=False,
        label=_lazy(u'Ready for localization'),
        required=False)

    needs_change = forms.BooleanField(
        label=_lazy(u'Needs change'),
        initial=False,
        required=False)

    needs_change_comment = forms.CharField(
        label=_lazy(u'Comment:'),
        widget=forms.Textarea(),
        required=False)


class AddContributorForm(forms.Form):
    """Form to add contributors to a document."""
    users = MultiUsernameField(
        widget=forms.TextInput(attrs={'placeholder': _lazy(u'username'),
                                      'class': 'user-autocomplete'}))
