from django import forms
from django.contrib import admin

from kitsune.users import monkeypatch
from kitsune.users.models import AccountEvent, Profile


class ProfileAdminForm(forms.ModelForm):
    delete_avatar = forms.BooleanField(
        required=False, help_text=("Check to remove the user's avatar.")
    )

    class Meta(object):
        model = Profile
        exclude = ()


class ProfileAdmin(admin.ModelAdmin):
    actions = None
    fieldsets = (
        (
            None,
            {
                "fields": [
                    "user",
                    "name",
                    "public_email",
                    ("avatar", "delete_avatar"),
                    "bio",
                    "is_fxa_migrated",
                    "fxa_uid",
                ],
            },
        ),
        (
            "Contact Info",
            {
                "fields": [
                    "website",
                    "twitter",
                    "community_mozilla_org",
                    "people_mozilla_org",
                    "matrix_handle",
                ],
                "classes": ["collapse"],
            },
        ),
        (
            "Location",
            {
                "fields": ["timezone", ("country", "city"), "locale"],
                "classes": ["collapse"],
            },
        ),
    )
    form = ProfileAdminForm
    list_display = ["full_user", "name", "get_products"]
    list_select_related = True
    list_filter = ["is_fxa_migrated", "country"]
    search_fields = ["user__username", "user__email", "name", "fxa_uid"]
    autocomplete_fields = ["user"]

    def get_products(self, obj):
        """Get a list of products that a user is subscribed to."""
        return ",".join([product.title for product in obj.products.all()])

    def has_delete_permission(self, request, obj=None):
        return False

    def full_user(self, obj):
        if obj.name:
            return "%s <%s>" % (obj.user.username, obj.name)
        else:
            return obj.user.username

    full_user.short_description = "User"

    def save_model(self, request, obj, form, change):
        delete_avatar = form.cleaned_data.pop("delete_avatar", False)
        if delete_avatar and obj.avatar:
            obj.avatar.delete()
        obj.save()


class AccountEventAdmin(admin.ModelAdmin):
    """Admin entry for SET tokens."""

    list_display = ["status", "event_type", "fxa_uid"]
    list_filter = (
        "event_type",
        "status",
    )
    autocomplete_fields = ["profile"]

    class Meta:
        model = AccountEvent


admin.site.register(Profile, ProfileAdmin)
admin.site.register(AccountEvent, AccountEventAdmin)
monkeypatch.patch_all()
