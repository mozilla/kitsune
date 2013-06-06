from django.contrib import admin

from kitsune.groups.models import GroupProfile


class GroupProfileAdmin(admin.ModelAdmin):
    raw_id_fields = ['leaders']

admin.site.register(GroupProfile, GroupProfileAdmin)
