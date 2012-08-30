from django.contrib import admin
from forums.models import Forum


class ForumAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'display_order', 'is_listed')
    list_display_links = ('name', 'slug')
    list_editable = ('display_order', 'is_listed')
    readonly_fields = ('id',)
    exclude = ('last_post',)
    prepopulated_fields = {'slug': ('name',)}

admin.site.register(Forum, ForumAdmin)
