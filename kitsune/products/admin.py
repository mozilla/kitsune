from django.contrib import admin

from kitsune.products.models import Product


class ProductAdmin(admin.ModelAdmin):
    list_display = ('title', 'slug', 'display_order', 'visible')
    list_display_links = ('title', 'slug')
    list_editable = ('display_order', 'visible')
    readonly_fields = ('id',)
    prepopulated_fields = {'slug': ('title',)}


admin.site.register(Product, ProductAdmin)
