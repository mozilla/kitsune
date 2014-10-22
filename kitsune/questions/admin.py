from django.contrib import admin

from kitsune.questions.models import QuestionLocale


class QuestionLocaleAdmin(admin.ModelAdmin):
    list_display = ('locale',)
    ordering = ('locale',)

admin.site.register(QuestionLocale, QuestionLocaleAdmin)
