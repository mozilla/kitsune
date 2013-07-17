from django.contrib import admin

from kitsune.dashboards.models import WikiMetric


class WikiMetricAdmin(admin.ModelAdmin):
    list_display = ['code', 'date', 'locale', 'product', 'value']
    list_filter = ['code', 'product', 'locale']


admin.site.register(WikiMetric, WikiMetricAdmin)
