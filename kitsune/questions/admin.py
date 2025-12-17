from django import forms
from django.conf import settings
from django.contrib import admin

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


class QuestionLocaleAdmin(admin.TabularInline):
    form = QuestionLocaleInlineForm
    model = AAQConfig.enabled_locales.through
    extra = 0


class AAQConfigAdmin(admin.ModelAdmin):
    form = AAQConfigForm
    list_display = ("title", "product", "is_active", "pinned_article_config")
    list_editable = ("is_active",)
    inlines = [QuestionLocaleAdmin]
    search_fields = ("title", "product__title", "product__slug")
    fields = (
        "title",
        "product",
        "is_active",
        "pinned_article_config",
        "associated_tags",
        "extra_fields",
    )
    autocomplete_fields = ("pinned_article_config",)


admin.site.register(AAQConfig, AAQConfigAdmin)
