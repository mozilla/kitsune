import itertools

import markdown
from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html_join
from django.utils.safestring import mark_safe

from kitsune.sumo.sanitize import RESTRICTED_HTML_ATTRIBUTES, RESTRICTED_HTML_TAGS, clean
from kitsune.wiki.models import (
    Document,
    ImportantDate,
    Locale,
    PinnedArticleConfig,
    RevisionTranslationRecord,
)


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
