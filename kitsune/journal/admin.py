from django.contrib import admin

from kitsune.journal.models import Record


class RecordAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "level",
        "src",
        "msg",
        "created",
    )
    list_filter = ("src",)


admin.site.register(Record, RecordAdmin)
