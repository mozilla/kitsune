from django.contrib import admin

from products.models import Product


class ProductAdmin(admin.ModelAdmin):
    list_display = ('title', 'display_order')
    list_display_links = ('title',)
    readonly_fields = ('id',)


admin.site.register(Product, ProductAdmin)
