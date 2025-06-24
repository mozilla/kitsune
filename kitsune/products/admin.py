from typing import Any

from django import forms
from django.contrib import admin
from django.db.models.query import QuerySet
from django.http import HttpRequest

from kitsune.products.models import (
    Platform,
    Product,
    ProductTopic,
    Topic,
    TopicSlugHistory,
    Version,
)


class DictOnlyJSONField(forms.JSONField):
    def to_python(self, value):
        if value in self.empty_values:
            return {}  # Convert an empty input value into an empty dict.
        result = super().to_python(value)
        if not isinstance(result, dict):
            raise forms.ValidationError("Value must be a JSON object (dict).")
        return result


class MetadataForm(forms.ModelForm):
    metadata = DictOnlyJSONField(required=False, initial=dict)

    class Meta:
        model = Topic
        fields = "__all__"


class ArchivedFilter(admin.SimpleListFilter):
    title = "Archived status"
    parameter_name = "is_archived"

    def lookups(
        self, request: HttpRequest, model_admin: admin.ModelAdmin
    ) -> list[tuple[str, str]]:
        return [("all", "All"), ("archived", "Yes"), ("not_archived", "No")]

    def queryset(self, request: HttpRequest, queryset: QuerySet[Any]) -> QuerySet[Any]:
        if self.value() == "archived":
            return queryset.filter(is_archived=True)
        if self.value() == "not_archived":
            return queryset.filter(is_archived=False)
        if self.value() == "all":
            return queryset
        return queryset

    def choices(self, changelist):
        for lookup, title in self.lookup_choices:
            yield {
                "selected": self.value() == lookup,
                "query_string": changelist.get_query_string({self.parameter_name: lookup}, []),
                "display": title,
            }


class ProductAdmin(admin.ModelAdmin):
    list_display = ("title", "slug", "display_order", "visible", "codename", "is_archived")
    list_display_links = ("title", "slug")
    list_editable = ("display_order", "visible", "is_archived")
    readonly_fields = ("id",)
    prepopulated_fields = {"slug": ("title",)}
    list_filter = (ArchivedFilter,)
    form = MetadataForm

    def changelist_view(self, request, extra_context=None):
        if "is_archived" not in request.GET:
            q = request.GET.copy()
            q["is_archived"] = "not_archived"
            request.GET = q
            request.META["QUERY_STRING"] = request.GET.urlencode()
        return super().changelist_view(request, extra_context=extra_context)


class ProductTopicInline(admin.TabularInline):
    model = ProductTopic
    extra = 1
    show_change_link = True


class TopicAdmin(admin.ModelAdmin):
    def parent(obj):
        return obj.parent

    def get_products(obj):
        return ", ".join([p.title for p in obj.products.all()])

    form = MetadataForm

    parent.short_description = "Parent"  # type: ignore
    get_products.short_description = "Products"  # type: ignore

    list_display = (
        "title",
        "slug",
        parent,
        get_products,
        "display_order",
        "visible",
        "in_aaq",
        "in_nav",
        "is_archived",
    )
    list_display_links = ("title", "slug")
    list_editable = ("display_order", "visible", "in_aaq", "in_nav", "is_archived")
    list_filter = (
        ArchivedFilter,
        "in_aaq",
        "parent",
        "slug",
    )
    inlines = [ProductTopicInline]
    search_fields = (
        "title",
        "slug",
        "products__title",
        "products__slug",
    )
    readonly_fields = ("id",)
    prepopulated_fields = {"slug": ("title",)}

    def changelist_view(self, request, extra_context=None):
        if "is_archived" not in request.GET:
            q = request.GET.copy()
            q["is_archived"] = "not_archived"
            request.GET = q
            request.META["QUERY_STRING"] = request.GET.urlencode()
        return super().changelist_view(request, extra_context=extra_context)


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
