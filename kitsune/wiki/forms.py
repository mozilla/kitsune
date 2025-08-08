import re

from django import forms
from django.conf import settings
from django.contrib.auth.models import Group
from django.template.defaultfilters import slugify
from django.utils.translation import gettext_lazy as _lazy
from django.utils.translation import ngettext_lazy as _nlazy

from kitsune.products.models import Product, Topic
from kitsune.sumo.form_fields import MultiUsernameField, MultiUsernameFilterField
from kitsune.wiki.config import CATEGORIES, SIGNIFICANCES
from kitsune.wiki.content_managers import ManualContentManager
from kitsune.wiki.models import MAX_REVISION_COMMENT_LENGTH, Document, DraftRevision, Revision
from kitsune.wiki.tasks import add_short_links
from kitsune.wiki.widgets import ProductsWidget, RelatedDocumentsWidget, TopicsWidget

TITLE_REQUIRED = _lazy("Please provide a title.")
TITLE_SHORT = _lazy(
    "The title is too short (%(show_value)s characters). "
    "It must be at least %(limit_value)s characters."
)
TITLE_LONG = _lazy(
    "Please keep the length of the title to %(limit_value)s "
    "characters or less. It is currently %(show_value)s "
    "characters."
)
SLUG_REQUIRED = _lazy("Please provide a slug.")
SLUG_INVALID = _lazy("The slug provided is not valid.")
SLUG_SHORT = _lazy(
    "The slug is too short (%(show_value)s characters). "
    "It must be at least %(limit_value)s characters."
)
SLUG_LONG = _lazy(
    "Please keep the length of the slug to %(limit_value)s "
    "characters or less. It is currently %(show_value)s "
    "characters."
)
SUMMARY_REQUIRED = _lazy("Please provide a summary.")
SUMMARY_SHORT = _lazy(
    "The summary is too short (%(show_value)s characters). "
    "It must be at least %(limit_value)s characters."
)
SUMMARY_LONG = _lazy(
    "Please keep the length of the summary to "
    "%(limit_value)s characters or less. It is currently "
    "%(show_value)s characters."
)
CONTENT_REQUIRED = _lazy("Please provide content.")
CONTENT_SHORT = _lazy(
    "The content is too short (%(show_value)s characters). "
    "It must be at least %(limit_value)s characters."
)
CONTENT_LONG = _lazy(
    "Please keep the length of the content to "
    "%(limit_value)s characters or less. It is currently "
    "%(show_value)s characters."
)
COMMENT_LONG = _lazy(
    "Please keep the length of the comment to "
    "%(limit_value)s characters or less. It is currently "
    "%(show_value)s characters."
)
PRODUCT_REQUIRED = _lazy("Please select at least one product.")
TOPIC_REQUIRED = _lazy("Please select at least one topic.")


class DocumentForm(forms.ModelForm):
    """Form to create/edit a document."""

    title = forms.CharField(
        min_length=5,
        max_length=255,
        widget=forms.TextInput(),
        label=_lazy("Title:"),
        help_text=_lazy("Title of article"),
        error_messages={
            "required": TITLE_REQUIRED,
            "min_length": TITLE_SHORT,
            "max_length": TITLE_LONG,
        },
    )

    # We don't use forms.SlugField because it is too strict in
    # what it allows (English/Roman alpha-numeric characters and dashes).
    # Instead, we do custom validation in `clean_slug` below.
    slug = forms.CharField(
        min_length=3,
        max_length=255,
        widget=forms.TextInput(),
        label=_lazy("Slug:"),
        help_text=_lazy("Article URL"),
        error_messages={
            "required": SLUG_REQUIRED,
            "min_length": SLUG_SHORT,
            "max_length": SLUG_LONG,
        },
    )

    is_localizable = forms.BooleanField(
        initial=True, label=_lazy("Allow translations:"), required=False
    )

    is_archived = forms.BooleanField(label=_lazy("Obsolete:"), required=False)

    restrict_to_groups = forms.ModelMultipleChoiceField(
        required=False,
        queryset=Group.objects.order_by("name").all(),
        label=_lazy("The document will be restricted to members of the selected group(s)."),
        help_text=_lazy("The document will be visible only to users in the selected group(s)."),
    )

    allow_discussion = forms.BooleanField(
        label=_lazy("Allow discussion on this article?"), initial=True, required=False
    )

    category = forms.ChoiceField(
        choices=CATEGORIES,
        # Required for non-translations, which is
        # enforced in Document.clean().
        required=False,
        label=_lazy("Category:"),
        help_text=_lazy("Type of article"),
    )

    topics = forms.MultipleChoiceField(
        label=_lazy("Select topic(s)"),
        required=False,
        widget=TopicsWidget(),
    )

    products = forms.MultipleChoiceField(
        label=_lazy("Select product(s)"),
        required=False,
        widget=ProductsWidget(),
    )

    related_documents = forms.MultipleChoiceField(
        label=_lazy("Related documents:"), required=False, widget=RelatedDocumentsWidget()
    )

    locale = forms.CharField(widget=forms.HiddenInput())

    needs_change = forms.BooleanField(label=_lazy("Needs change:"), initial=False, required=False)

    needs_change_comment = forms.CharField(
        label=_lazy("Comment:"), widget=forms.Textarea(), required=False
    )

    def clean_slug(self):
        slug = self.cleaned_data["slug"]
        # Blacklist /, ?, % and +,
        if not re.compile(r"^[^/^\+^\?%]+$").match(slug):
            raise forms.ValidationError(SLUG_INVALID)
        return slug

    def clean(self):
        cdata = super().clean()
        locale = cdata.get("locale")

        # Products are required for en-US
        product_ids = set(map(int, cdata.get("products", [])))
        if locale == settings.WIKI_DEFAULT_LANGUAGE and (not product_ids or len(product_ids) < 1):
            raise forms.ValidationError(PRODUCT_REQUIRED)

        # Topics are required for en-US
        topic_ids = set(map(int, cdata.get("topics", [])))
        if locale == settings.WIKI_DEFAULT_LANGUAGE and (not topic_ids or len(topic_ids) < 1):
            raise forms.ValidationError(TOPIC_REQUIRED)

        invalid_topics = []
        for topic in Topic.active.filter(id__in=topic_ids):
            topic_product_ids = set(topic.products.values_list("id", flat=True))
            if not product_ids.issubset(topic_product_ids):
                invalid_topics.append(topic)

        invalid_products = []
        for product in Product.active.filter(id__in=product_ids):
            product_topic_ids = set(product.m2m_topics.values_list("id", flat=True))
            if not topic_ids.issubset(product_topic_ids):
                invalid_products.append(product)

        error_message = ""
        if invalid_topics or invalid_products:
            invalid_items = (
                invalid_products if len(invalid_topics) > len(invalid_products) else invalid_topics
            )
            invalid_item_names = ", ".join([item.title for item in invalid_items])

            error_message = _nlazy(
                (
                    f"The following {'product' if invalid_items is invalid_products else 'topic'} "
                    f"is not associated with all selected "
                    f"{'topics' if invalid_items is invalid_products else 'products'}: %(items)s"
                ),
                (
                    f"The following {'products' if invalid_items is invalid_products else 'topics'} "
                    f"are not associated with all selected "
                    f"{'topics' if invalid_items is invalid_products else 'products'}: %(items)s"
                ),
                len(invalid_items),
            ) % {"items": invalid_item_names}

            if error_message:
                raise forms.ValidationError(error_message)

        return cdata

    class Meta:
        model = Document
        fields = (
            "title",
            "slug",
            "category",
            "is_localizable",
            "products",
            "topics",
            "locale",
            "is_archived",
            "allow_discussion",
            "needs_change",
            "needs_change_comment",
            "related_documents",
            "restrict_to_groups",
        )

    def __init__(self, *args, **kwargs):
        # Quasi-kwargs:
        can_archive = kwargs.pop("can_archive", False)
        can_edit_needs_change = kwargs.pop("can_edit_needs_change", False)
        initial_title = kwargs.pop("initial_title", "")

        super().__init__(*args, **kwargs)

        title_field = self.fields["title"]
        title_field.initial = initial_title

        slug_field = self.fields["slug"]
        slug_field.initial = slugify(initial_title)

        topics_field = self.fields["topics"]
        topics_field.choices = Topic.active.values_list("id", "title")

        products_field = self.fields["products"]
        products_field.choices = Product.active.values_list("id", "title")

        related_documents_field = self.fields["related_documents"]
        related_documents_field.choices = Document.objects.values_list("id", "title")

        # If user hasn't permission to frob is_archived, remove the field. This
        # causes save() to skip it as well.
        if not can_archive:
            del self.fields["is_archived"]

        # If user hasn't permission to mess with needs_change*, remove the
        # fields. This causes save() to skip it as well.
        if not can_edit_needs_change:
            del self.fields["needs_change"]
            del self.fields["needs_change_comment"]

    def save(self, parent_doc, **kwargs):
        """Persist the Document form, and return the saved Document."""
        doc = super().save(commit=False, **kwargs)
        doc.parent = parent_doc

        # If document doesn't need change, clear out the comment.
        if not doc.needs_change:
            doc.needs_change_comment = ""

        # Create the share link if it doesn't exist and is in
        # a category it should show for.
        doc.save()
        if doc.category in settings.IA_DEFAULT_CATEGORIES and not doc.share_link:
            # This operates under the constraints of passing in a list.
            add_short_links.delay([doc.pk])

        self.save_m2m()

        if parent_doc:
            # Products are not set on translations.
            doc.products.remove(*list(doc.products.all()))
            # A child always inherits parent topics.
            doc.topics.add(*list(parent_doc.topics.all()))

        return doc


class RevisionForm(forms.ModelForm):
    """Form to create new revisions."""

    keywords = forms.CharField(
        required=False,
        label=_lazy("Keywords:"),
        help_text=_lazy("Affects search results"),
    )

    summary = forms.CharField(
        min_length=5,
        max_length=1000,
        widget=forms.Textarea(),
        label=_lazy("Search result summary:"),
        help_text=_lazy("Only displayed on search results page"),
        error_messages={
            "required": SUMMARY_REQUIRED,
            "min_length": SUMMARY_SHORT,
            "max_length": SUMMARY_LONG,
        },
    )

    content = forms.CharField(
        min_length=5,
        max_length=100000,
        label=_lazy("Content:"),
        widget=forms.Textarea(),
        error_messages={
            "required": CONTENT_REQUIRED,
            "min_length": CONTENT_SHORT,
            "max_length": CONTENT_LONG,
        },
    )

    expires = forms.DateField(label=_lazy("Expiry date:"), required=False)

    comment = forms.CharField(required=False, label=_lazy("Comment:"))

    class Meta:
        model = Revision
        fields = ("keywords", "summary", "content", "comment", "based_on", "expires")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["based_on"].widget = forms.HiddenInput()
        self.fields["comment"].widget = forms.TextInput(
            attrs={"maxlength": MAX_REVISION_COMMENT_LENGTH}
        )

    def save(self, creator, document, based_on_id=None, base_rev=None, **kwargs):
        """Persist me, and return the saved Revision.

        Take several other necessary pieces of data that aren't from the
        form.

        """
        data = self.cleaned_data.copy()
        content_manager = ManualContentManager()
        return content_manager.create_revision(
            data=data,
            document=document,
            creator=creator,
            based_on_id=based_on_id,
            base_rev=base_rev,
            send_notifications=True,
        )


class DraftRevisionForm(forms.ModelForm):
    class Meta:
        model = DraftRevision
        fields = ("keywords", "summary", "content", "slug", "title", "based_on")

    def save(self, request):
        """save the draft revision and return the draft revision"""
        creator = request.user
        doc_data = self.cleaned_data
        parent_doc = doc_data["based_on"].document
        locale = request.LANGUAGE_CODE

        return ManualContentManager().save_draft(creator, parent_doc, locale, doc_data)


class ReviewForm(forms.Form):
    comment = forms.CharField(
        max_length=2000,
        widget=forms.Textarea(),
        required=False,
        label=_lazy("Comment:"),
        error_messages={"max_length": COMMENT_LONG},
    )

    _widget = forms.RadioSelect()
    significance = forms.TypedChoiceField(
        label=_lazy("Significance:"),
        choices=SIGNIFICANCES,
        initial=SIGNIFICANCES[1][0],
        required=False,
        widget=_widget,
        coerce=int,
        empty_value=SIGNIFICANCES[1][0],
    )

    is_ready_for_localization = forms.BooleanField(
        initial=False, label=_lazy("Ready for localization"), required=False
    )

    needs_change = forms.BooleanField(label=_lazy("Needs change"), initial=False, required=False)

    needs_change_comment = forms.CharField(
        label=_lazy("Comment:"), widget=forms.Textarea(), required=False
    )


class AddContributorForm(forms.Form):
    """Form to add contributors to a document."""

    users = MultiUsernameField(
        widget=forms.TextInput(
            attrs={"placeholder": _lazy("username"), "class": "user-autocomplete"}
        )
    )


languages = [("", "Any")] + [
    (lang[0], "{1} ({0})".format(*lang)) for lang in settings.LANGUAGE_CHOICES
]


class RevisionFilterForm(forms.Form):
    """Form to filter a list of revisions."""

    locale = forms.ChoiceField(label=_lazy("Locale:"), choices=languages, required=False)
    users = MultiUsernameFilterField(label=_lazy("Users:"), required=False)
    start = forms.DateField(label=_lazy("Start:"), required=False)
    end = forms.DateField(label=_lazy("End:"), required=False)
