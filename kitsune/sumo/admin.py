from django.contrib import admin


class LogEntryAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "content_type",
        "object_id",
        "object_repr",
        "change_message",
    )
    list_filter = (
        "user",
        "content_type",
    )


admin.site.register(admin.models.LogEntry, LogEntryAdmin)
