from django.contrib import admin

from kitsune.questions.models import QuestionLocale, AAQConfig


class QuestionLocaleAdmin(admin.ModelAdmin):
    list_display = ("locale",)
    ordering = ("locale",)
    filter_horizontal = ("products",)


admin.site.register(QuestionLocale, QuestionLocaleAdmin)


class AAQConfigAdmin(admin.ModelAdmin):
    list_display = ("product",)
    autocomplete_fields = ("pinned_articles",)


admin.site.register(AAQConfig, AAQConfigAdmin)
