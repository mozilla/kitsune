from django import forms
from django.contrib import admin

from kitsune.products.models import Platform, Product, Topic, Version


class ProductAdminForm(forms.ModelForm):

    class Meta:
        model = Product
        fields = '__all__'

    def clean(self, *args, **kwargs):
        """Do not allow products with the same name or slug."""
        products = Product.objects.all()
        cdata = super(ProductAdminForm, self).clean(*args, **kwargs)
        slug = cdata.get('slug', '')
        title = cdata.get('title', '')
        if ((slug and products.filter(slug=slug).exists()) or
                (title and products.filter(title=title).exists())):
            raise forms.ValidationError('Slug and title must be unique within products.')
        return cdata


class ProductAdmin(admin.ModelAdmin):
    form = ProductAdminForm
    list_display = ('title', 'slug', 'display_order', 'visible', 'codename', 'parent',)
    list_display_links = ('title', 'slug')
    list_editable = ('display_order', 'visible')
    readonly_fields = ('id',)
    prepopulated_fields = {'slug': ('title',)}

    def formfield_for_foreignkey(self, db_field, request, **kwargs):

        # remove products that already have a parent in the dropdown menu
        if db_field.name == 'parent':
            kwargs['queryset'] = Product.objects.filter(parent__isnull=True)
        return super(ProductAdmin, self).formfield_for_foreignkey(db_field, request, **kwargs)


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
