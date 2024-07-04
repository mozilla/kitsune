from typing import Any

from django.contrib import admin
from django.db.models.query import QuerySet
from django.http import HttpRequest

from kitsune.products.models import Platform, Product, Topic, TopicSlugHistory, Version


class ArchivedFilter(admin.SimpleListFilter):
    title = "Archived status"
    parameter_name = "is_archived"

    def lookups(
        self, request: HttpRequest, model_admin: admin.ModelAdmin
    ) -> list[tuple[str, str]]:
        return [("archived", "Yes"), ("not_archived", "No")]

    def queryset(self, request: HttpRequest, queryset: QuerySet[Any]) -> QuerySet[Any]:
        if self.value() == "archived":
            return queryset.filter(is_archived=True)
        if self.value() == "not_archived":
            return queryset.filter(is_archived=False)
        return queryset


class ProductAdmin(admin.ModelAdmin):
    list_display = ("title", "slug", "display_order", "visible", "codename", "is_archived")
    list_display_links = ("title", "slug")
    list_editable = ("display_order", "visible", "is_archived")
    readonly_fields = ("id",)
    prepopulated_fields = {"slug": ("title",)}
    list_filter = (ArchivedFilter,)


class TopicAdmin(admin.ModelAdmin):
    def parent(obj):
        return obj.parent

    parent.short_description = "Parent"  # type: ignore

    list_display = (
        "product",
        "title",
        "slug",
        parent,
        "display_order",
        "visible",
        "in_aaq",
        "is_archived",
    )
    list_display_links = ("title", "slug")
    list_editable = ("display_order", "visible", "in_aaq", "is_archived")
    list_filter = (
        ArchivedFilter,
        "product",
        "parent",
        "slug",
    )
    search_fields = (
        "title",
        "slug",
        "product__title",
        "product__slug",
    )
    readonly_fields = ("id",)
    prepopulated_fields = {"slug": ("title",)}


class VersionAdmin(admin.ModelAdmin):
    list_display = ("name", "product", "slug", "min_version", "max_version", "visible", "default")
    list_display_links = ("name",)
    list_editable = ("slug", "visible", "default", "min_version", "max_version")
    list_filter = ("product",)


class PlatformAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "display_order", "visible")
    list_display_links = ("name",)
    list_editable = ("slug", "display_order", "visible")


class TopicSlugHistoryAdmin(admin.ModelAdmin):
    list_display = ("topic", "slug", "created")
    list_display_links = ("topic", "slug")
    list_filter = ("topic",)
    search_fields = ("topic__title", "slug")
    verbose_name_plural = "Topic Slug History"


admin.site.register(Platform, PlatformAdmin)
admin.site.register(Product, ProductAdmin)
admin.site.register(Topic, TopicAdmin)
admin.site.register(Version, VersionAdmin)
admin.site.register(TopicSlugHistory, TopicSlugHistoryAdmin)
