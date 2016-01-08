import re

from django import forms
from django.conf import settings
from django.template.defaultfilters import slugify
from django.utils.translation import ugettext_lazy as _lazy

from kitsune.products.models import Product, Topic
from kitsune.sumo.form_fields import MultiUsernameField, StrippedCharField
from kitsune.wiki.config import SIGNIFICANCES, CATEGORIES
from kitsune.wiki.models import (
    Document, Revision, DraftRevision, MAX_REVISION_COMMENT_LENGTH)
from kitsune.wiki.tasks import add_short_links
from kitsune.wiki.widgets import (
    RadioFieldRendererWithHelpText,
    ProductTopicsAndSubtopicsWidget,
    RelatedDocumentsWidget)


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
PRODUCT_REQUIRED = _lazy(u'Please select at least one product.')
TOPIC_REQUIRED = _lazy(u'Please select at least one topic.')


class DocumentForm(forms.ModelForm):
    """Form to create/edit a document."""
    def __init__(self, *args, **kwargs):
        # Quasi-kwargs:
        can_archive = kwargs.pop('can_archive', False)
        can_edit_needs_change = kwargs.pop('can_edit_needs_change', False)
        initial_title = kwargs.pop('initial_title', '')

        super(DocumentForm, self).__init__(*args, **kwargs)

        title_field = self.fields['title']
        title_field.initial = initial_title

        slug_field = self.fields['slug']
        slug_field.initial = slugify(initial_title)

        topics_field = self.fields['topics']
        topics_field.choices = Topic.objects.values_list('id', 'title')

        products_field = self.fields['products']
        products_field.choices = Product.objects.values_list('id', 'title')

        related_documents_field = self.fields['related_documents']
        related_documents_field.choices = Document.objects.values_list('id', 'title')

        # If user hasn't permission to frob is_archived, remove the field. This
        # causes save() to skip it as well.
        if not can_archive:
            del self.fields['is_archived']

        # If user hasn't permission to mess with needs_change*, remove the
        # fields. This causes save() to skip it as well.
        if not can_edit_needs_change:
            del self.fields['needs_change']
            del self.fields['needs_change_comment']

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

    products = forms.MultipleChoiceField(
        label=_lazy(u'Relevant to:'),
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
        widget=ProductTopicsAndSubtopicsWidget())

    related_documents = forms.MultipleChoiceField(
        label=_lazy(u'Related documents:'),
        required=False,
        widget=RelatedDocumentsWidget())

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
        # Blacklist /, ?, % and +,
        if not re.compile(r'^[^/^\+^\?%]+$').match(slug):
            raise forms.ValidationError(SLUG_INVALID)
        return slug

    def clean(self):
        c = super(DocumentForm, self).clean()
        locale = c.get('locale')

        # Products are required for en-US
        products = c.get('products')
        if (locale == settings.WIKI_DEFAULT_LANGUAGE and
                (not products or len(products) < 1)):
            raise forms.ValidationError(PRODUCT_REQUIRED)

        # Topics are required for en-US
        topics = c.get('topics')
        if (locale == settings.WIKI_DEFAULT_LANGUAGE and
                (not topics or len(topics) < 1)):
            raise forms.ValidationError(TOPIC_REQUIRED)

        return c

    class Meta:
        model = Document
        fields = ('title', 'slug', 'category', 'is_localizable', 'products',
                  'topics', 'locale', 'is_archived', 'allow_discussion',
                  'needs_change', 'needs_change_comment', 'related_documents')

    def save(self, parent_doc, **kwargs):
        """Persist the Document form, and return the saved Document."""
        doc = super(DocumentForm, self).save(commit=False, **kwargs)
        doc.parent = parent_doc

        # If document doesn't need change, clear out the comment.
        if not doc.needs_change:
            doc.needs_change_comment = ''

        # Create the share link if it doesn't exist and is in
        # a category it should show for.
        doc.save()
        if (doc.category in settings.IA_DEFAULT_CATEGORIES and
                not doc.share_link):
            # This operates under the constraints of passing in a list.
            add_short_links.delay([doc.pk])

        self.save_m2m()

        if parent_doc:
            # Products are not set on translations.
            doc.products.remove(*[p for p in doc.products.all()])

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

    content = StrippedCharField(
        min_length=5, max_length=100000,
        label=_lazy(u'Content:'),
        widget=forms.Textarea(),
        error_messages={'required': CONTENT_REQUIRED,
                        'min_length': CONTENT_SHORT,
                        'max_length': CONTENT_LONG})

    expires = forms.DateField(
        label=_lazy(u'Expiry date:'),
        required=False)

    comment = StrippedCharField(required=False, label=_lazy(u'Comment:'))

    class Meta(object):
        model = Revision
        fields = ('keywords', 'summary', 'content', 'comment', 'based_on',
                  'expires')

    def __init__(self, *args, **kwargs):
        super(RevisionForm, self).__init__(*args, **kwargs)
        self.fields['based_on'].widget = forms.HiddenInput()
        self.fields['comment'].widget = forms.TextInput(
            attrs={'maxlength': MAX_REVISION_COMMENT_LENGTH})

    def save(self, creator, document, based_on_id=None, base_rev=None,
             **kwargs):
        """Persist me, and return the saved Revision.

        Take several other necessary pieces of data that aren't from the
        form.

        """
        # Throws a TypeError if somebody passes in a commit kwarg:
        new_rev = super(RevisionForm, self).save(commit=False, **kwargs)

        new_rev.document = document
        new_rev.creator = creator

        if based_on_id:
            new_rev.based_on_id = based_on_id

        # If the document doesn't allow the revision creator to edit the
        # keywords, keep the old value.
        if base_rev and not document.allows(creator, 'edit_keywords'):
            new_rev.keywords = base_rev.keywords

        new_rev.save()
        return new_rev


class DraftRevisionForm(forms.ModelForm):
    class Meta(object):
        model = DraftRevision
        fields = ('keywords', 'summary', 'content', 'slug', 'title', 'based_on')

    def save(self, request):
        """save the draft revision and return the draft revision"""
        creator = request.user
        doc_data = self.cleaned_data
        parent_doc = doc_data['based_on'].document
        locale = request.LANGUAGE_CODE
        draft, created = DraftRevision.objects.update_or_create(
            creator=creator, document=parent_doc, locale=locale, defaults=doc_data)
        return draft


class ReviewForm(forms.Form):
    comment = StrippedCharField(max_length=2000, widget=forms.Textarea(),
                                required=False, label=_lazy(u'Comment:'),
                                error_messages={'max_length': COMMENT_LONG})

    _widget = forms.RadioSelect(renderer=RadioFieldRendererWithHelpText)
    significance = forms.TypedChoiceField(
        label=_lazy(u'Significance:'),
        choices=SIGNIFICANCES,
        initial=SIGNIFICANCES[1][0],
        required=False,
        widget=_widget,
        coerce=int, empty_value=SIGNIFICANCES[1][0])

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


languages = [('', 'Any')] + [(l[0], u'{1} ({0})'.format(*l))
                             for l in settings.LANGUAGE_CHOICES]


class RevisionFilterForm(forms.Form):
    """Form to filter a list of revisions."""
    locale = forms.ChoiceField(label=_lazy(u'Locale:'), choices=languages,
                               required=False)
    users = MultiUsernameField(label=_lazy(u'Users:'), required=False)
    start = forms.DateField(label=_lazy(u'Start:'), required=False)
    end = forms.DateField(label=_lazy(u'End:'), required=False)
