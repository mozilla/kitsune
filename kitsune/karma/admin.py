from django.contrib import admin

from kitsune.karma.models import Title


class TitleAdmin(admin.ModelAdmin):
    raw_id_fields = ("users", "groups")
    exclude = ("is_auto",)

    def queryset(self, request):
        qs = super(TitleAdmin, self).queryset(request)
        return qs.filter(is_auto=False)


admin.site.register(Title, TitleAdmin)
