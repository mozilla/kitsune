from django.contrib import admin

from announcements.models import Announcement


class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ['__unicode__', 'is_visible']
    exclude = ['created']
    readonly_fields = ['creator']

    def is_visible(self, obj):
        visible = obj.is_visible()
        if visible and obj.show_until:
            return 'Yes (until %s)' % obj.show_until
        elif visible:
            return 'Yes (always)'
        return ''
    is_visible.short_description = 'Visible?'

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.creator = request.user
        obj.save()


admin.site.register(Announcement, AnnouncementAdmin)
