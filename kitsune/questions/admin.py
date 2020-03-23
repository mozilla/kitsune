from django.contrib import admin

from kitsune.questions.models import QuestionLocale


class QuestionLocaleAdmin(admin.ModelAdmin):
    list_display = ("locale",)
    ordering = ("locale",)
    filter_horizontal = ("products",)


admin.site.register(QuestionLocale, QuestionLocaleAdmin)
