from django.contrib import admin

from kitsune.tidings.models import Watch, WatchFilter


class FilterInline(admin.TabularInline):
    model = WatchFilter


class WatchAdmin(admin.ModelAdmin):
    list_filter = ["content_type", "event_type"]
    raw_id_fields = ["user"]
    inlines = [FilterInline]


class WatchFilterAdmin(admin.ModelAdmin):
    list_filter = ["name"]
    raw_id_fields = ["watch"]


admin.site.register(Watch, WatchAdmin)
admin.site.register(WatchFilter, WatchFilterAdmin)
