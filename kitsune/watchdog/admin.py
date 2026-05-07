from django.contrib import admin

from kitsune.watchdog.models import TaskHealth


class TaskHealthAdmin(admin.ModelAdmin):
    list_display = ("name", "last_completed_at", "created_at")
    search_fields = ("name",)
    ordering = ("last_completed_at",)
    readonly_fields = ("name", "created_at", "last_completed_at")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


admin.site.register(TaskHealth, TaskHealthAdmin)
