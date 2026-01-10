from django.contrib import admin

from kitsune.groups.models import GroupProfile


class GroupProfileAdmin(admin.ModelAdmin):
    raw_id_fields = ["leaders"]
    list_display = ["group", "slug", "is_private"]
    list_filter = ["is_private"]


admin.site.register(GroupProfile, GroupProfileAdmin)
