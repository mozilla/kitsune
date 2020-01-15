from django.contrib import admin

from kitsune.dashboards.models import WikiMetric


class WikiMetricAdmin(admin.ModelAdmin):
    list_display = [
        'code', 'date', 'locale',
        'locale_code', 'product', 'value'
    ]
    list_filter = ['code', 'product', 'locale']
    date_hierarchy = 'date'

    def locale_code(self, obj):
        return obj.locale

    locale_code.short_description = "Locale Code"


admin.site.register(WikiMetric, WikiMetricAdmin)
