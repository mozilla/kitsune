from datetime import timedelta

from django import forms
from django.conf import settings
from django.contrib import admin
from django.core.exceptions import ValidationError
from django.core.validators import validate_slug
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.html import format_html


from kitsune.l10n.models import (
    RevisionActivityRecord,
    LANGUAGE_CHOICES_EXCLUDING_DEFAULT,
    MachineTranslationConfiguration,
    MachineTranslationServiceRecord,
)
from kitsune.l10n.utils import duration_to_text, text_to_duration


class SimpleDurationField(forms.DurationField):
    def prepare_value(self, value):
        if isinstance(value, timedelta):
            return duration_to_text(value)
        return value

    def to_python(self, value):
        if value in self.empty_values:
            return None
        if isinstance(value, timedelta):
            return value
        try:
            value = text_to_duration(str(value))
        except OverflowError:
            raise ValidationError(
                self.error_messages["overflow"].format(
                    min_days=timedelta.min.days, max_days=timedelta.max.days
                ),
                code="overflow",
            )
        if value is None:
            raise ValidationError(self.error_messages["invalid"], code="invalid")
        return value


class MultipleSlugField(forms.Field):
    widget = forms.Textarea(
        attrs=dict(
            rows=3,
            placeholder=(
                'Enter each slug on a new line. Slugs that end with "*" will match as a prefix.'
            ),
        )
    )

    def prepare_value(self, value):
        if isinstance(value, list):
            return "\n".join(value)
        return value

    def to_python(self, value):
        if not value:
            return []

        result, errors = [], []
        for slug in value.splitlines():
            if not slug.strip():
                continue
            try:
                if slug.count("*") > 1:
                    raise ValidationError("")
                validate_slug(slug.rstrip("*"))
            except ValidationError:
                if not errors:
                    errors.append(
                        "A valid slug consists of letters, numbers, underscores or hyphens, "
                        'but may end with "*" to match as a prefix.'
                    )
                errors.append(f"'{slug}' is not a valid slug.")
            else:
                result.append(slug)

        if errors:
            raise ValidationError(errors)
        return result


class MachineTranslationConfigurationForm(forms.ModelForm):

    heartbeat_period = SimpleDurationField()
    review_grace_period = SimpleDurationField()
    post_review_grace_period = SimpleDurationField(label="Post-review grace period")
    locale_team_inactivity_grace_period = SimpleDurationField(
        label="Locale-team inactivity grace period"
    )
    enabled_languages = forms.MultipleChoiceField(
        choices=LANGUAGE_CHOICES_EXCLUDING_DEFAULT,
        widget=forms.CheckboxSelectMultiple,
        label="Languages enabled for machine translation",
        required=False,
    )
    limit_to_slugs = MultipleSlugField(
        label="Limit machine translation to these KB article slugs",
        required=False,
    )
    disabled_slugs = MultipleSlugField(
        label="Disable machine translation for these KB article slugs",
        required=False,
    )

    class Meta:
        model = MachineTranslationConfiguration
        fields = "__all__"


@admin.register(MachineTranslationConfiguration)
class MachineTranslationConfigurationAdmin(admin.ModelAdmin):
    list_display = (
        "is_enabled",
        "llm_name",
        "heartbeat_period",
        "review_grace_period",
        "post_review_grace_period",
        "locale_team_inactivity_grace_period",
        "enabled_languages",
        "limit_to_slugs",
        "disabled_slugs",
        "limit_to_approved_after",
        "limit_to_approver_in_group",
    )

    form = MachineTranslationConfigurationForm

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def changelist_view(self, request, extra_context=None):
        obj = MachineTranslationConfiguration.load()
        return redirect(
            reverse("admin:l10n_machinetranslationconfiguration_change", args=[obj.id])
        )


class MachineTranslationServiceRecordLocaleFilter(admin.SimpleListFilter):
    title = "Target Locale"
    parameter_name = "target_locale"

    def lookups(self, request, model_admin):
        return [
            (locale, f"{settings.LOCALES[locale].english} ({locale})")
            for locale in MachineTranslationServiceRecord.objects.values_list(
                "target_locale", flat=True
            ).distinct()
        ]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(target_locale=self.value())
        return queryset


@admin.register(MachineTranslationServiceRecord)
class MachineTranslationServiceRecordAdmin(admin.ModelAdmin):

    exclude = ("source_revision", "details")
    list_display = (
        "created",
        "target_locale",
        "source_revision_link",
        "source_attribute",
        "service",
        "model_name",
    )
    list_filter = (
        MachineTranslationServiceRecordLocaleFilter,
        "created",
        "service",
        "model_name",
    )
    readonly_fields = (
        "created",
        "target_locale",
        "source_revision_link",
        "source_attribute",
        "service",
        "model_name",
        "llm_input",
        "llm_output",
        "langchain_model_configuration",
    )
    ordering = (
        "-created",
        "target_locale",
        "source_revision",
        "source_attribute",
        "service",
        "model_name",
    )

    @admin.display(description="LLM input")
    def llm_input(self, obj):
        return "\n\n".join(obj.details["input"])

    @admin.display(description="LLM output")
    def llm_output(self, obj):
        return obj.details["output"]

    @admin.display(description="LangChain model configuration")
    def langchain_model_configuration(self, obj):
        return "\n".join(f"{k}: {v}" for k, v in obj.details["model_info"].items())

    @admin.display(description="Source revision")
    def source_revision_link(self, obj):
        rev = obj.source_revision
        doc = rev.document
        return format_html(
            '<a href="{}">[{}] {} (#{})</a>',
            rev.get_absolute_url(),
            doc.locale,
            doc.title,
            rev.id,
        )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class RevisionActivityRecordLocaleFilter(admin.SimpleListFilter):
    title = "Locale"
    parameter_name = "locale"

    def lookups(self, request, model_admin):
        return [
            (locale, f"{settings.LOCALES[locale].english} ({locale})")
            for locale in RevisionActivityRecord.objects.values_list(
                "revision__document__locale", flat=True
            ).distinct()
        ]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(revision__document__locale=self.value())
        return queryset


@admin.register(RevisionActivityRecord)
class RevisionActivityRecordAdmin(admin.ModelAdmin):
    exclude = ("revision",)
    list_select_related = ("revision",)
    list_display = ("revision_link", "action", "action_timestamp")
    list_filter = (RevisionActivityRecordLocaleFilter, "action")
    readonly_fields = ("revision_link", "action", "action_timestamp")

    @admin.display(description="Timestamp of Action")
    def action_timestamp(self, obj):
        return obj.action_timestamp

    @admin.display(description="Revision")
    def revision_link(self, obj):
        rev = obj.revision
        doc = rev.document
        return format_html(
            '<a href="{}">[{}] {} (#{})</a>',
            rev.get_absolute_url(),
            doc.locale,
            doc.title,
            rev.id,
        )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
