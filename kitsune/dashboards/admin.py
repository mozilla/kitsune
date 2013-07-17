from django.contrib import admin

from kitsune.dashboards.models import WikiMetric, WikiMetricKind


class WikiMetricAdmin(admin.ModelAdmin):
    list_display = ['kind', 'date', 'locale', 'product', 'value']
    list_filter = ['kind', 'product', 'locale']


class WikiMetricKindAdmin(admin.ModelAdmin):
    pass


admin.site.register(WikiMetric, WikiMetricAdmin)
admin.site.register(WikiMetricKind, WikiMetricKindAdmin)
