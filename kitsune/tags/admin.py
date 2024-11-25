from django.contrib import admin

from kitsune.tags.models import SumoTag


@admin.register(SumoTag)
class SumoTagAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    search_fields = ("name", "slug")
