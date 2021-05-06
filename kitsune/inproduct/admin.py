from django.contrib import admin

from kitsune.inproduct.models import Redirect


class RedirectAdmin(admin.ModelAdmin):
    list_display = ("product", "version", "platform", "locale", "topic", "target")
    list_display_links = ("topic", "target")
    list_filter = ("product", "version", "platform", "locale")
    search_fields = ("topic", "target")


admin.site.register(Redirect, RedirectAdmin)
