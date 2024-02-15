from django.conf import settings
from django.contrib import admin
from django.db.models import Case, Exists, F, OuterRef, Value, When
from django.db.models.functions import Substr
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from kitsune.inproduct.models import Redirect
from kitsune.wiki.models import Document


class KBLinkFilter(admin.SimpleListFilter):
    title = _("KB article")
    parameter_name = "kb_article"

    def lookups(self, request, model_admin):
        return (
            ("with_kb", _("KB Article Exists")),
            ("without_kb", _("No KB Article Exists")),
        )

    def queryset(self, request, queryset):
        qs = queryset.annotate(
            kb_slug=Case(
                When(target__startswith="kb/", then=Substr("target", 4)),
                When(target__startswith="/kb/", then=Substr("target", 5)),
                default=None,
            ),
            kb_locale=Case(
                When(locale="", then=Value(settings.WIKI_DEFAULT_LANGUAGE)),
                default=F("locale"),
            ),
        ).filter(kb_slug__isnull=False)
        doc_exists = Exists(
            Document.objects.filter(slug=OuterRef("kb_slug"), locale=OuterRef("kb_locale"))
        )
        if self.value() == "with_kb":
            # Filter for objects with a KB link
            return qs.filter(doc_exists)
        if self.value() == "without_kb":
            # Filter for KB objects without a KB link
            return qs.exclude(doc_exists)


class RedirectAdmin(admin.ModelAdmin):
    list_display = (
        "product",
        "version",
        "platform",
        "locale",
        "topic",
        "target",
        "kb_link",
    )
    list_display_links = ("topic", "target")
    list_filter = ("product", "version", "platform", "locale", KBLinkFilter)
    search_fields = ("topic", "target")

    @admin.display(description="KB Article")
    def kb_link(self, obj):
        target = obj.target.lstrip("/")
        if not target.startswith("kb/"):
            return None

        slug = target.split("/")[-1]
        locale = obj.locale if obj.locale else settings.WIKI_DEFAULT_LANGUAGE

        try:
            doc = Document.objects.get(slug=slug, locale=locale)
        except Document.DoesNotExist:
            return None
        else:
            target_url = doc.get_absolute_url()
        return format_html('<a href="{}">{}</a>', target_url, target_url)


admin.site.register(Redirect, RedirectAdmin)
