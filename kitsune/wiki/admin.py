import itertools

import markdown
from django import forms
from django.contrib import admin
from django.db.models import Count, Exists, OuterRef
from django.urls import reverse
from django.utils.html import format_html_join
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _lazy

from kitsune.sumo.sanitize import RESTRICTED_HTML_ATTRIBUTES, RESTRICTED_HTML_TAGS, clean
from kitsune.wiki.config import DEFAULT_AUDIENCE_SLUG
from kitsune.wiki.models import (
    Audience,
    AudienceFeaturedDocument,
    Document,
    DocumentAudience,
    ImportantDate,
    Locale,
    PinnedArticleConfig,
    RevisionTranslationRecord,
)


class NoAudienceFilter(admin.SimpleListFilter):
    title = _lazy("knowledge base")
    parameter_name = "audience"

    def lookups(self, request, model_admin):
        return (("none", _lazy("No knowledge base")),)

    def queryset(self, request, queryset):
        if self.value() == "none":
            return queryset.filter(
                ~Exists(DocumentAudience.objects.filter(document=OuterRef("pk"))),
                parent__isnull=True,
            )
        return queryset


class DocumentAdmin(admin.ModelAdmin):
    exclude = ("tags",)
    list_display = (
        "locale",
        "title",
        "display_order",
        "category",
        "is_localizable",
        "is_archived",
        "allow_discussion",
    )
    list_display_links = ("title",)
    list_editable = ("display_order",)
    list_filter = (
        "is_template",
        "is_localizable",
        "category",
        "locale",
        "is_archived",
        "allow_discussion",
        "topics",
        NoAudienceFilter,
    )
    raw_id_fields = ("parent", "contributors")
    readonly_fields = ("id", "current_revision", "latest_localizable_revision")
    search_fields = ("title",)

    def has_add_permission(self, request):
        return False

    @staticmethod
    def _set_archival(queryset, should_be_archived):
        """Set archival bit of documents, percolating up to parents as well."""
        for doc in queryset:
            # If this is a child, change its parent instead, and saving the
            # parent will change all the children to match.
            doc_to_change = doc.parent or doc
            doc_to_change.is_archived = should_be_archived
            doc_to_change.save()

    def _show_archival_message(self, request, queryset, verb):
        count = len(queryset)
        phrase = (
            "document, along with its English version or translations, was marked as "
            if count == 1
            else "documents, along with their English versions or translations, were marked as "
        )
        self.message_user(request, "{} {} {}.".format(count, phrase, verb))

    def archive(self, request, queryset):
        """Mark several documents as obsolete."""
        self._set_archival(queryset, True)
        self._show_archival_message(request, queryset, "obsolete")

    archive.short_description = "Mark as obsolete"  # type: ignore

    def unarchive(self, request, queryset):
        """Mark several documents as not obsolete."""
        self._set_archival(queryset, False)
        self._show_archival_message(request, queryset, "no longer obsolete")

    unarchive.short_description = "Mark as not obsolete"  # type: ignore

    def allow_discussion(self, request, queryset):
        """Allow discussion on several documents."""
        queryset.update(allow_discussion=True)
        self.message_user(request, "Document(s) now allow discussion.")

    def disallow_discussion(self, request, queryset):
        """Disallow discussion on several documents."""
        queryset.update(allow_discussion=False)
        self.message_user(request, "Document(s) no longer allow discussion.")

    actions = [archive, unarchive, allow_discussion, disallow_discussion]


admin.site.register(Document, DocumentAdmin)


class AudienceAdminForm(forms.ModelForm):
    confirm_publish = forms.BooleanField(
        required=False,
        label=_lazy("Publish its articles"),
        help_text=_lazy(
            "Making this knowledge base public makes every article in it readable by everyone."
        ),
    )

    class Meta:
        model = Audience
        fields = "__all__"

    def clean(self):
        cleaned_data = super().clean()
        # Read-only fields are missing from cleaned_data; the instance still holds old values.
        is_public = cleaned_data.get("is_public", self.instance.is_public)
        if is_public and cleaned_data.get("groups"):
            self.add_error("groups", _lazy("A public knowledge base cannot have groups."))
        if cleaned_data.get("slug") == DEFAULT_AUDIENCE_SLUG and not is_public:
            self.add_error("is_public", _lazy("The default knowledge base is always public."))
        if (
            is_public
            and self.instance.pk
            and not self.instance.is_public
            and self.instance.documents.exists()
            and not cleaned_data.get("confirm_publish")
        ):
            self.add_error(
                "confirm_publish", _lazy("Confirm that its articles become readable by everyone.")
            )
        return cleaned_data


class AudienceFeaturedDocumentForm(forms.ModelForm):
    class Meta:
        model = AudienceFeaturedDocument
        fields = ("document", "order")

    def clean(self):
        cleaned_data = super().clean()
        document = cleaned_data.get("document")
        # The inline formset sets "audience_id" on the instance; it is empty for a new KB.
        if document is not None and not (
            document.parent_id is None
            and self.instance.audience_id
            and document.audiences.filter(pk=self.instance.audience_id).exists()
        ):
            self.add_error(
                "document",
                _lazy("Choose an original article that is assigned to this knowledge base."),
            )
        return cleaned_data


class AudienceFeaturedDocumentInline(admin.TabularInline):
    model = AudienceFeaturedDocument
    form = AudienceFeaturedDocumentForm
    raw_id_fields = ("document",)
    max_num = 3

    def get_formset(self, request, obj=None, **kwargs):
        # Without it the admin accepts submitted rows beyond max_num.
        kwargs["validate_max"] = True
        return super().get_formset(request, obj, **kwargs)


class AudienceAdmin(admin.ModelAdmin):
    form = AudienceAdminForm
    inlines = [AudienceFeaturedDocumentInline]
    list_display = ("name", "slug", "is_public", "document_count")

    def get_inlines(self, request, obj):
        # A new knowledge base has no articles to feature yet.
        return self.inlines if obj is not None else []

    def get_fields(self, request, obj=None):
        fields = ["name", "slug", "is_public", "groups"]
        if obj is not None and not obj.is_public:
            fields.append("confirm_publish")
        return [
            *fields,
            "is_listed",
            "description",
            "color",
            "mark",
            "support_text",
            "support_link_text",
            "support_url",
        ]

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(document_count=Count("documents"))

    @admin.display(description=_lazy("Documents"), ordering="document_count")
    def document_count(self, obj):
        return obj.document_count

    def get_readonly_fields(self, request, obj=None):
        if obj is None:
            return ()
        return ("slug", "is_public") if obj.slug == DEFAULT_AUDIENCE_SLUG else ("slug",)

    def has_delete_permission(self, request, obj=None):
        if obj is not None and obj.slug == DEFAULT_AUDIENCE_SLUG:
            return False
        return super().has_delete_permission(request, obj)

    def delete_queryset(self, request, queryset):
        super().delete_queryset(request, queryset.exclude(slug=DEFAULT_AUDIENCE_SLUG))


admin.site.register(Audience, AudienceAdmin)


class ImportantDateAdmin(admin.ModelAdmin):
    list_display = ("text", "date")
    list_display_links = ("text", "date")
    list_filter = ("text", "date")
    raw_id_fields = ()
    readonly_fields = ("id",)
    search_fields = ("text", "date")


admin.site.register(ImportantDate, ImportantDateAdmin)


class LocaleAdmin(admin.ModelAdmin):
    list_display = ("locale",)
    list_display_links = ("locale",)
    raw_id_fields = ("leaders", "reviewers", "editors")
    search_fields = ("locale",)


admin.site.register(Locale, LocaleAdmin)


class PinnedArticleConfigAdmin(admin.ModelAdmin):
    list_display = ("title", "use_for_home_page", "used_by")
    ordering = ("title", "id")
    autocomplete_fields = ("pinned_articles",)
    search_fields = ("title", "pinned_articles__title")
    readonly_fields = ("used_by",)

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related("products", "aaq_configs")

    @admin.display(description="Used By")
    def used_by(self, obj):
        """
        Return links to the products and AAQ configs associated with this configuration.
        """
        return format_html_join(
            ", ",
            '<a href="{}">{}</a>',
            (
                itertools.chain(
                    (
                        (reverse("admin:products_product_change", args=[p.pk]), p.title)
                        for p in obj.products.all()
                    ),
                    (
                        (reverse("admin:questions_aaqconfig_change", args=[a.pk]), a.title)
                        for a in obj.aaq_configs.all()
                    ),
                )
            ),
        )


class RevisionTranslationRecordAdmin(admin.ModelAdmin):
    """Read-only view of the LLM explanations recorded for AI/hybrid translations."""

    list_display = ("revision", "locale", "method", "trigger", "created")
    list_filter = ("locale", "method", "trigger", "created")
    search_fields = ("revision__document__title", "revision__document__slug")
    fieldsets = (
        (None, {"fields": ("revision", "locale", "method", "trigger", "created")}),
        (
            "LLM Explanations",
            {
                "fields": (
                    "content_explanation",
                    "summary_explanation",
                    "keywords_explanation",
                    "title_explanation",
                )
            },
        ),
    )
    readonly_fields = (
        "revision",
        "locale",
        "method",
        "trigger",
        "created",
        "content_explanation",
        "summary_explanation",
        "keywords_explanation",
        "title_explanation",
    )

    @admin.display(description="Content")
    def content_explanation(self, obj):
        return self.render_explanation(obj, "content")

    @admin.display(description="Summary")
    def summary_explanation(self, obj):
        return self.render_explanation(obj, "summary")

    @admin.display(description="Keywords")
    def keywords_explanation(self, obj):
        return self.render_explanation(obj, "keywords")

    @admin.display(description="Title")
    def title_explanation(self, obj):
        return self.render_explanation(obj, "title")

    @staticmethod
    def render_explanation(obj, key):
        """Render a single attribute's explanation, or an em dash if absent."""
        text = (obj.explanation or {}).get(key)
        if text:
            # The LLM often uses markdown in its explanation.
            html = markdown.markdown(text, extensions=["fenced_code"])
            return mark_safe(
                clean(html, tags=RESTRICTED_HTML_TAGS, attributes=RESTRICTED_HTML_ATTRIBUTES)
            )

        return "—"

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("revision__document")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


admin.site.register(PinnedArticleConfig, PinnedArticleConfigAdmin)
admin.site.register(RevisionTranslationRecord, RevisionTranslationRecordAdmin)
