from django.contrib import admin

from kitsune.products.models import Platform, Product, Topic, Version


class ProductAdmin(admin.ModelAdmin):
    list_display = ('title', 'slug', 'display_order', 'visible', 'codename')
    list_display_links = ('title', 'slug')
    list_editable = ('display_order', 'visible')
    readonly_fields = ('id',)
    prepopulated_fields = {'slug': ('title',)}


class TopicAdmin(admin.ModelAdmin):
    def parent(obj):
        return obj.parent
    parent.short_description = 'Parent'

    list_display = ('product', 'title', 'slug', parent, 'display_order', 'visible', 'in_aaq')
    list_display_links = ('title', 'slug')
    list_editable = ('display_order', 'visible', 'in_aaq')
    list_filter = ('product', 'parent', 'slug')
    readonly_fields = ('id',)
    prepopulated_fields = {'slug': ('title',)}


class VersionAdmin(admin.ModelAdmin):
    list_display = ('name', 'product', 'slug', 'min_version', 'max_version',
                    'visible', 'default')
    list_display_links = ('name',)
    list_editable = ('slug', 'visible', 'default', 'min_version',
                     'max_version')
    list_filter = ('product', )


class PlatformAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'display_order', 'visible')
    list_display_links = ('name', )
    list_editable = ('slug', 'display_order', 'visible')


admin.site.register(Platform, PlatformAdmin)
admin.site.register(Product, ProductAdmin)
admin.site.register(Topic, TopicAdmin)
admin.site.register(Version, VersionAdmin)
