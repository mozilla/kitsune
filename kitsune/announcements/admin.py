from django.contrib import admin

from kitsune.announcements.models import Announcement


class AnnouncementAdmin(admin.ModelAdmin):
    list_display = [
        "__str__",
        "get_groups",
        "get_platforms",
        "locale",
        "product",
        "creator",
        "is_visible",
    ]
    exclude = ["created"]
    readonly_fields = ["creator"]
    date_hierarchy = "created"
    list_filter = ["created", "groups", "platforms", "locale", "product"]
    search_fields = ["creator__username"]

    def get_groups(self, obj):
        groups = obj.groups.all()
        if groups:
            return ", ".join([g.name for g in groups])
        return ""

    get_groups.short_description = "Groups"  # type: ignore

    def get_platforms(self, obj):
        platforms = obj.platforms.all()
        if platforms:
            return ", ".join([p.name for p in platforms])
        return ""

    get_platforms.short_description = "Platforms"  # type: ignore

    def is_visible(self, obj):
        visible = obj.is_visible()
        if visible and obj.show_until:
            return "Yes (until {})".format(obj.show_until)
        elif visible:
            return "Yes (always)"
        return ""

    is_visible.short_description = "Visible?"  # type: ignore

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.creator = request.user
        obj.save()

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "product":
            kwargs["queryset"] = db_field.related_model.objects.filter(is_archived=False)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


admin.site.register(Announcement, AnnouncementAdmin)
