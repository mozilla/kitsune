from typing import Any

from django import forms
from django.contrib import admin
from django.contrib.admin.utils import unquote
from django.db.models.query import QuerySet
from django.forms.models import BaseInlineFormSet
from django.http import HttpRequest
from django.utils.translation import gettext_lazy as _lazy

from kitsune.groups.membership import lock_enterprise_hierarchy
from kitsune.groups.models import GroupProfile
from kitsune.groups.onboarding import get_enterprise_root, link_zendesk_organization
from kitsune.products.models import (
    CuratedBlock,
    CuratedBlockItem,
    Platform,
    Product,
    ProductSupportConfig,
    ProductTopic,
    SupportContract,
    SupportCoverage,
    SupportOrganization,
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
        "codename",
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
        "article_ordering",
        "visible",
        "in_aaq",
        "in_nav",
        "is_archived",
    )
    list_display_links = ("title", "slug")
    list_editable = (
        "display_order",
        "article_ordering",
        "visible",
        "in_aaq",
        "in_nav",
        "is_archived",
    )
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
    list_display = ("form_title", "slug", "config_count")
    list_display_links = ("form_title", "slug")
    search_fields = ("form_title", "slug")
    prepopulated_fields = {"slug": ("form_title",)}

    @admin.display(description="# Configs")
    def config_count(self, obj):
        return obj.zendesk_configs.count()


class ZendeskConfigAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "ticket_form_id",
        "enable_urgency_field",
        "enable_os_field",
        "enable_deployment_fields",
        "skip_spam_moderation",
        "topic_count",
    )
    list_display_links = ("name",)
    list_editable = (
        "enable_urgency_field",
        "enable_os_field",
        "enable_deployment_fields",
        "skip_spam_moderation",
    )
    list_filter = (
        "enable_urgency_field",
        "enable_os_field",
        "enable_deployment_fields",
        "skip_spam_moderation",
    )
    search_fields = ("name",)
    inlines = [ZendeskTopicConfigurationInline]

    @admin.display(description="# Topics")
    def topic_count(self, obj):
        return obj.topic_configurations.count()


class SupportOrganizationInlineFormSet(BaseInlineFormSet):
    """Reject nested groups submitted together for one configuration.

    The model's ``clean()`` checks each row against saved rows; this catches the same
    conflict between rows in the same submission.
    """

    def clean(self):
        super().clean()
        seen = []
        for form in self.forms:
            if not hasattr(form, "cleaned_data") or form.cleaned_data.get("DELETE"):
                continue
            group = form.cleaned_data.get("group")
            if group is None:
                continue
            profile = GroupProfile.objects.filter(group=group).first()
            if profile is None:
                continue
            for other_group, other_profile in seen:
                if profile.path.startswith(other_profile.path) or other_profile.path.startswith(
                    profile.path
                ):
                    raise forms.ValidationError(
                        f"'{group.name}' and '{other_group.name}' are nested. Configure one "
                        f"of them, not both."
                    )
            seen.append((group, profile))


class SupportOrganizationInline(admin.TabularInline):
    model = SupportOrganization
    formset = SupportOrganizationInlineFormSet
    extra = 0
    autocomplete_fields = ("group",)


class ProductSupportConfigAdmin(admin.ModelAdmin):
    inlines = (SupportOrganizationInline,)
    list_display = (
        "product",
        "is_active",
        "enable_forum_support",
        "enable_zendesk_support",
        "is_hybrid",
        "default_support_type",
        "subscription_only",
    )
    list_display_links = ("product",)
    list_editable = ("is_active",)
    list_filter = ("is_active", "default_support_type")
    search_fields = ("product__title", "product__slug")
    autocomplete_fields = (
        "product",
        "forum_config",
        "zendesk_config",
        "unsubscribed_redirect_product",
    )
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
                "description": "Set default support type for all users and optionally for organization members.",
            },
        ),
        (
            "Subscription Routing",
            {
                "fields": ("subscription_only", "unsubscribed_redirect_product"),
                "description": (
                    "When subscription_only is enabled, only users with an active product subscription "
                    "can access support. Unsubscribed users are redirected to the specified product's AAQ, "
                    "or the entire AAQ flow returns 404 if no redirect product is set."
                ),
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
                f"<li><strong>{topic.slug}</strong>: {topic.form_title}{loginless_badge}</li>"
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
    search_fields = ("zendesk_config__name", "zendesk_topic__form_title", "zendesk_topic__slug")


class CuratedBlockItemInlineFormSet(BaseInlineFormSet):
    """Validate the items the block will hold once this submission is saved."""

    def clean(self):
        super().clean()
        if any(self.errors):
            return
        deleted_forms = self.deleted_forms
        items = [
            form.instance
            for form in self.forms
            if form not in deleted_forms and (form.has_changed() or form.instance.pk)
        ]
        self.instance.clean_items(items)


class CuratedBlockItemInline(admin.TabularInline):
    model = CuratedBlockItem
    formset = CuratedBlockItemInlineFormSet
    extra = 1
    fields = ("position", "document", "question")
    autocomplete_fields = ("document", "question")


class CuratedBlockAdmin(admin.ModelAdmin):
    list_display = (
        "product",
        "topic",
        "kind",
        "variant",
        "show_until",
        "updated_at",
        "updated_by",
    )
    list_filter = ("product", "topic", "kind")
    search_fields = ("topic__title", "product__title")
    list_select_related = ("product", "topic", "updated_by")
    fields = (
        "product",
        "topic",
        "kind",
        "variant",
        "message",
        "show_until",
        "updated_by",
        "updated_at",
    )
    readonly_fields = ("updated_by", "updated_at")
    autocomplete_fields = ("product", "topic")
    inlines = (CuratedBlockItemInline,)

    def get_readonly_fields(self, request, obj=None):
        if obj is None:
            return self.readonly_fields
        return (*self.readonly_fields, "product", "topic", "kind")

    def formfield_for_choice_field(self, db_field, request, **kwargs):
        if db_field.name == "variant":
            kwargs["help_text"] = (
                "Manual questions stop showing once they are archived, "
                "180 days after they were asked."
            )
        return super().formfield_for_choice_field(db_field, request, **kwargs)

    def save_model(self, request, obj, form, change):
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


admin.site.register(ZendeskTopic, ZendeskTopicAdmin)
admin.site.register(ZendeskConfig, ZendeskConfigAdmin)
admin.site.register(ZendeskTopicConfiguration, ZendeskTopicConfigurationAdmin)
admin.site.register(ProductSupportConfig, ProductSupportConfigAdmin)
admin.site.register(CuratedBlock, CuratedBlockAdmin)


class SupportContractForm(forms.ModelForm):
    class Meta:
        model = SupportContract
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if "company" in self.fields:
            company = self.fields["company"]
            try:
                company.queryset = get_enterprise_root().get_children().select_related("group")
            except forms.ValidationError:
                company.queryset = GroupProfile.objects.none()
            company.widget.can_add_related = False
            company.widget.can_change_related = False
            company.widget.can_delete_related = False
            company.widget.can_view_related = False

    def clean(self):
        cleaned_data = super().clean()
        starts_on = cleaned_data.get("starts_on")
        ends_on = cleaned_data.get("ends_on")
        if starts_on and ends_on and starts_on > ends_on:
            self.add_error("ends_on", _lazy("The end date must be on or after the start date."))
        return cleaned_data


class SupportCoverageInlineFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()
        if any(self.errors):
            return
        product_ids = set()
        submitted_ids = {form.instance.pk for form in self.forms if form.instance.pk is not None}
        for form in self.forms:
            if not form.cleaned_data:
                continue
            if form.instance.pk and "product" in form.changed_data:
                raise forms.ValidationError(
                    _lazy(
                        "The product of a saved coverage cannot be changed. To fix a mistake, "
                        "cancel the contract and enter a new one."
                    )
                )
            product_ids.add(form.cleaned_data["product"].pk)
        if self.instance.pk:
            product_ids.update(
                self.instance.coverages.exclude(pk__in=submitted_ids).values_list(
                    "product_id", flat=True
                )
            )

        contract = self.instance
        blocking_statuses = (SupportContract.Status.ACTIVE, SupportContract.Status.SUSPENDED)
        if (
            contract.status not in blocking_statuses
            or not contract.company_id
            or not contract.starts_on
            or not contract.ends_on
            or contract.starts_on > contract.ends_on
            or not product_ids
        ):
            return
        if (
            SupportCoverage.objects.filter(
                product_id__in=product_ids,
                contract__company_id=contract.company_id,
                contract__status__in=blocking_statuses,
                contract__starts_on__lte=contract.ends_on,
                contract__ends_on__gte=contract.starts_on,
            )
            .exclude(contract_id=contract.pk)
            .exists()
        ):
            raise forms.ValidationError(
                _lazy(
                    "Another active or suspended contract already covers a selected product "
                    "during this period."
                )
            )


class SupportCoverageInline(admin.TabularInline):
    model = SupportCoverage
    formset = SupportCoverageInlineFormSet
    extra = 1
    min_num = 1
    can_delete = False
    autocomplete_fields = ("product", "zendesk_config")

    def get_formset(self, request, obj=None, **kwargs):
        return super().get_formset(request, obj, validate_min=True, **kwargs)

    def has_view_permission(self, request, obj=None):
        parent_admin = self.admin_site.get_model_admin(self.parent_model)
        return parent_admin.has_view_permission(request, obj)

    def has_add_permission(self, request, obj=None):
        parent_admin = self.admin_site.get_model_admin(self.parent_model)
        if obj is None:
            return parent_admin.has_add_permission(request)
        return parent_admin.has_change_permission(request, obj)

    def has_change_permission(self, request, obj=None):
        parent_admin = self.admin_site.get_model_admin(self.parent_model)
        return parent_admin.has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        return False


def lock_contract_company(company_id):
    try:
        company_id = int(company_id)
    except TypeError, ValueError:
        return
    GroupProfile.objects.select_for_update().filter(pk=company_id).first()


class SupportContractAdmin(admin.ModelAdmin):
    form = SupportContractForm
    fields = ("company", "name", "status", "starts_on", "ends_on")
    inlines = (SupportCoverageInline,)
    list_display = ("name", "company", "status", "starts_on", "ends_on")
    list_filter = ("status",)
    search_fields = ("company__slug", "company__group__name", "name")

    def get_readonly_fields(self, request, obj=None):
        return ("company",) if obj else ()

    def has_delete_permission(self, request, obj=None):
        return False

    def changeform_view(self, request, object_id=None, form_url="", extra_context=None):
        if request.method != "POST":
            return super().changeform_view(request, object_id, form_url, extra_context)
        if "_saveasnew" in request.POST:
            object_id = None
        with lock_enterprise_hierarchy():
            if object_id is not None:
                contract = self.get_object(request, unquote(object_id))
                company_id = contract.company_id if contract else None
            else:
                company_id = request.POST.get("company")
            lock_contract_company(company_id)
            return super().changeform_view(request, object_id, form_url, extra_context)

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        link_zendesk_organization(obj.company, None)


admin.site.register(SupportContract, SupportContractAdmin)
