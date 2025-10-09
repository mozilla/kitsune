from django import forms
from django.conf import settings
from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from kitsune.questions.models import AAQConfig, QuestionLocale
from kitsune.sumo.utils import PrettyJSONEncoder


class AAQConfigForm(forms.ModelForm):
    extra_fields = forms.JSONField(encoder=PrettyJSONEncoder)

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
    list_display = ("title", "product", "is_active", "pinned_articles")
    list_editable = ("is_active",)
    inlines = [QuestionLocaleAdmin]
    fields = (
        "title",
        "product",
        "is_active",
        "associated_tags",
        "extra_fields",
        "pinned_articles",
    )
    readonly_fields = ("pinned_articles",)

    @admin.display(description="Pinned Articles")
    def pinned_articles(self, obj):
        """
        Show a link to the related PinnedArticleConfig if there is one.
        """
        if config := obj.pinned_article_config.first():
            url = reverse("admin:wiki_pinnedarticleconfig_change", args=[config.pk])
            return format_html(f'<a href="{url}">{config}</a>')

        return format_html(
            f'<a class="addlink" href="{reverse("admin:wiki_pinnedarticleconfig_add")}">Add</a>'
        )


admin.site.register(AAQConfig, AAQConfigAdmin)
