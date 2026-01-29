from typing import Any

from django import forms
from django.contrib import admin
from django.db.models.query import QuerySet
from django.http import HttpRequest

from kitsune.products.models import (
    Platform,
    Product,
    ProductSupportConfig,
    ProductTopic,
    Topic,
    TopicSlugHistory,
    Version,
    ZendeskConfig,
    ZendeskTopic,
    ZendeskTopicConfiguration,
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
    list_display = (
        "title",
        "slug",
        "display_order",
        "visible",
        "is_archived",
        "pinned_article_config",
    )
    list_display_links = ("title", "slug")
    list_editable = ("display_order", "visible", "is_archived")
    readonly_fields = ("id",)
    prepopulated_fields = {"slug": ("title",)}
    list_filter = (ArchivedFilter,)
    search_fields = ("title", "slug")
    form = MetadataForm
    autocomplete_fields = ("pinned_article_config",)

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
    def parent(self):
        return self.parent

    def get_products(self):
        return ", ".join([p.title for p in self.products.all()])

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


class ZendeskTopicConfigurationInline(admin.TabularInline):
    """
    Inline editor for topic-to-config associations.
    Shows which topics are included in this config with their settings.
    """

    model = ZendeskTopicConfiguration
    extra = 1
    autocomplete_fields = ("zendesk_topic",)
    fields = ("zendesk_topic", "display_order", "loginless_only")
    ordering = ("display_order",)


class ZendeskTopicAdmin(admin.ModelAdmin):
    list_display = ("topic", "slug", "config_count")
    list_display_links = ("topic", "slug")
    search_fields = ("topic", "slug")
    prepopulated_fields = {"slug": ("topic",)}

    @admin.display(description="# Configs")
    def config_count(self, obj):
        return obj.zendesk_configs.count()


class ZendeskConfigAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "ticket_form_id",
        "enable_os_field",
        "skip_spam_moderation",
        "topic_count",
    )
    list_display_links = ("name",)
    list_editable = ("enable_os_field", "skip_spam_moderation")
    list_filter = ("enable_os_field", "skip_spam_moderation")
    search_fields = ("name",)
    inlines = [ZendeskTopicConfigurationInline]

    @admin.display(description="# Topics")
    def topic_count(self, obj):
        return obj.topic_configurations.count()


class ProductSupportConfigAdmin(admin.ModelAdmin):
    list_display = (
        "product",
        "is_active",
        "enable_forum_support",
        "enable_zendesk_support",
        "is_hybrid",
        "default_support_type",
    )
    list_display_links = ("product",)
    list_editable = ("is_active",)
    list_filter = ("is_active", "default_support_type")
    search_fields = ("product__title", "product__slug")
    filter_horizontal = ("hybrid_support_groups",)
    autocomplete_fields = ("product", "forum_config", "zendesk_config")
    readonly_fields = (
        "is_hybrid",
        "enable_forum_support",
        "enable_zendesk_support",
        "zendesk_topics_display",
        "zendesk_config_link",
    )

    fieldsets = (
        (
            "Basic Information",
            {
                "fields": ("product", "is_active"),
            },
        ),
        (
            "Support Channels",
            {
                "fields": (
                    "forum_config",
                    "zendesk_config",
                    "zendesk_config_link",
                    "zendesk_topics_display",
                    "enable_forum_support",
                    "enable_zendesk_support",
                    "is_hybrid",
                ),
                "description": "Configure which support channels are available for this product. "
                "At least one must be selected.",
            },
        ),
        (
            "Routing Configuration",
            {
                "fields": ("default_support_type", "group_default_support_type"),
                "description": "Set default support type for all users and optionally for hybrid group members.",
            },
        ),
        (
            "Hybrid Support (Forums + Zendesk)",
            {
                "fields": ("hybrid_support_groups",),
                "description": "Users in these groups can choose between forums and Zendesk when both are enabled. "
                "Leave empty to allow all users to choose.",
            },
        ),
    )

    @admin.display(boolean=True, description="Forum Enabled")
    def enable_forum_support(self, obj):
        return obj.enable_forum_support

    @admin.display(boolean=True, description="Zendesk Enabled")
    def enable_zendesk_support(self, obj):
        return obj.enable_zendesk_support

    @admin.display(boolean=True, description="Hybrid (Both)")
    def is_hybrid(self, obj):
        return obj.is_hybrid

    @admin.display(description="Zendesk Config Details")
    def zendesk_config_link(self, obj):
        from django.urls import reverse
        from django.utils.html import format_html

        if not obj.zendesk_config:
            return "—"

        url = reverse("admin:products_zendeskconfig_change", args=[obj.zendesk_config.pk])
        return format_html(
            '<a href="{}" target="_blank">{}</a> (click to edit topics)',
            url,
            obj.zendesk_config.name,
        )

    @admin.display(description="Available Topics")
    def zendesk_topics_display(self, obj):
        from django.utils.html import format_html

        if not obj.zendesk_config:
            return "—"

        topic_configs = obj.zendesk_config.topic_configurations.all().select_related(
            "zendesk_topic"
        )
        if not topic_configs:
            return format_html("<em>No topics configured</em>")

        topic_items = []
        for topic_config in topic_configs:
            topic = topic_config.zendesk_topic
            loginless_badge = (
                " <span style='color: #666;'>(loginless only)</span>"
                if topic_config.loginless_only
                else ""
            )
            topic_items.append(
                f"<li><strong>{topic.slug}</strong>: {topic.topic}{loginless_badge}</li>"
            )

        return format_html(
            "<ul style='margin: 0; padding-left: 20px;'>{}</ul>", "".join(topic_items)
        )


class ZendeskTopicConfigurationAdmin(admin.ModelAdmin):
    list_display = ("zendesk_config", "zendesk_topic", "display_order", "loginless_only")
    list_display_links = ("zendesk_config", "zendesk_topic")
    list_filter = ("zendesk_config", "loginless_only")
    list_editable = ("display_order", "loginless_only")
    autocomplete_fields = ("zendesk_config", "zendesk_topic")
    search_fields = ("zendesk_config__name", "zendesk_topic__topic", "zendesk_topic__slug")


admin.site.register(ZendeskTopic, ZendeskTopicAdmin)
admin.site.register(ZendeskConfig, ZendeskConfigAdmin)
admin.site.register(ZendeskTopicConfiguration, ZendeskTopicConfigurationAdmin)
admin.site.register(ProductSupportConfig, ProductSupportConfigAdmin)
