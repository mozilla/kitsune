from django.contrib import admin
from django.contrib.admin import ModelAdmin

from kitsune.dashboards.models import GroupDashboard


class GroupDashboardAdmin(ModelAdmin):
    list_display = ('group', 'dashboard', 'parameters')
    list_filter = ('group', 'dashboard')
    search_fields = ('dashboard', 'parameters')
admin.site.register(GroupDashboard, GroupDashboardAdmin)
