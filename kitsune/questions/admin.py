from django import forms
from django.conf import settings
from django.contrib import admin
from django.forms import BaseInlineFormSet

from kitsune.questions.models import AAQConfig, QuestionLocale
from kitsune.sumo.utils import PrettyJSONEncoder


class AAQConfigForm(forms.ModelForm):
    extra_fields = forms.JSONField(
        initial=list,
        required=False,
        encoder=PrettyJSONEncoder,
    )

    class Meta:
        model = AAQConfig
        fields = "__all__"


class QuestionLocaleInlineForm(forms.ModelForm):
    locale = forms.ChoiceField(
        choices=settings.LANGUAGE_CHOICES_ENGLISH,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields["locale"].initial = self.instance.questionlocale.locale

    def save(self, commit=True):
        locale_code = self.cleaned_data["locale"]
        if self.has_changed() and self.instance:
            question_locale, _ = QuestionLocale.objects.get_or_create(locale=locale_code)
            self.instance.questionlocale = question_locale
        super().save(commit)

        return self.instance

    class Meta:
        model = QuestionLocale
        fields = ["locale"]


class QuestionLocaleInlineFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()

        # Calculate how many locales actually remain after deletions.
        num_locales = self.total_form_count() - len(self.deleted_forms)

        active_configs = self.instance.support_configs.filter(is_active=True)

        if (num_locales == 0) and self.instance.pk and active_configs.exists():
            product_names = ", ".join(active_configs.values_list("product__title", flat=True))
            raise forms.ValidationError(
                "Cannot remove all enabled locales. This configuration is used "
                f"by product support configuration(s) for: {product_names}. "
                "Remove this forum configuration from those configurations first."
            )


class QuestionLocaleAdmin(admin.TabularInline):
    form = QuestionLocaleInlineForm
    formset = QuestionLocaleInlineFormSet
    model = AAQConfig.enabled_locales.through
    extra = 0


class AAQConfigAdmin(admin.ModelAdmin):
    form = AAQConfigForm
    list_display = ("title", "pinned_article_config", "used_by_products")
    inlines = [QuestionLocaleAdmin]
    search_fields = ("title",)
    fields = (
        "title",
        "pinned_article_config",
        "associated_tags",
        "extra_fields",
    )
    autocomplete_fields = ("pinned_article_config",)
    readonly_fields = ("used_by_products",)

    @admin.display(description="Used by products")
    def used_by_products(self, obj):
        if not obj.pk:
            return "-"
        products = obj.support_configs.select_related("product").values_list(
            "product__title", flat=True
        )
        return ", ".join(products) if products else "-"


admin.site.register(AAQConfig, AAQConfigAdmin)
