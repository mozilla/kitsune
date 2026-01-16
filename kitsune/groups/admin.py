from django.contrib import admin
from treebeard.admin import TreeAdmin
from treebeard.forms import movenodeform_factory

from kitsune.groups.models import GroupProfile


class GroupProfileAdmin(TreeAdmin):
    form = movenodeform_factory(GroupProfile)
    list_display = ["slug", "group", "visibility", "depth", "numchild"]
    list_filter = ["visibility"]
    raw_id_fields = ["leaders"]
    search_fields = ["slug", "group__name"]


admin.site.register(GroupProfile, GroupProfileAdmin)
