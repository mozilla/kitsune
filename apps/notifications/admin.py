from django.contrib import admin

from notifications.models import EventWatch, Watch, WatchFilter


class EventWatchAdmin(admin.ModelAdmin):
    list_filter = ['content_type', 'event_type', 'locale']


class FilterInline(admin.TabularInline):
    model = WatchFilter


class WatchAdmin(admin.ModelAdmin):
    list_filter = ['content_type', 'event_type']
    raw_id_fields = ['user']
    inlines = [FilterInline]


class WatchFilterAdmin(admin.ModelAdmin):
    list_filter = ['name']
    raw_id_fields = ['watch']


admin.site.register(EventWatch, EventWatchAdmin)
admin.site.register(Watch, WatchAdmin)
admin.site.register(WatchFilter, WatchFilterAdmin)
