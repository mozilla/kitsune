from django import forms
from django.contrib import admin

from kitsune.users import monkeypatch
from kitsune.users.models import Profile


class ProfileAdminForm(forms.ModelForm):
    delete_avatar = forms.BooleanField(required=False, help_text=(
        "Check to remove the user's avatar."))

    class Meta(object):
        model = Profile
        exclude = ()


class ProfileAdmin(admin.ModelAdmin):
    actions = None
    fieldsets = (
        (None, {
            'fields': ['user', 'name', 'public_email',
                       ('avatar', 'delete_avatar'), 'bio', 'is_fxa_migrated',
                       'fxa_uid', 'has_subscriptions'],
        }),
        ('Contact Info', {
            'fields': ['website', 'twitter', 'facebook', 'mozillians', 'irc_handle'],
            'classes': ['collapse'],
        }),
        ('Location', {
            'fields': ['timezone', ('country', 'city'), 'locale'],
            'classes': ['collapse'],
        }),
    )
    form = ProfileAdminForm
    list_display = ['full_user', 'name']
    list_select_related = True
    list_filter = ['is_fxa_migrated', 'country']
    search_fields = ['user__username', 'user__email', 'name']

    # This reduces the load to the db.
    readonly_fields = ['user']

    def has_delete_permission(self, request, obj=None):
        return False

    def full_user(self, obj):
        if obj.name:
            return u'%s <%s>' % (obj.user.username, obj.name)
        else:
            return obj.user.username
    full_user.short_description = 'User'

    def save_model(self, request, obj, form, change):
        delete_avatar = form.cleaned_data.pop('delete_avatar', False)
        if delete_avatar and obj.avatar:
            obj.avatar.delete()
        obj.save()


admin.site.register(Profile, ProfileAdmin)
monkeypatch.patch_all()
