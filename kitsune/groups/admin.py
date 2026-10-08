from django import forms
from django.conf import settings
from django.contrib import admin, messages
from django.core.exceptions import ValidationError
from django.http import HttpResponseBadRequest
from treebeard.admin import TreeAdmin
from treebeard.forms import movenodeform_factory

from kitsune.groups.membership import (
    lock_enterprise_hierarchy,
    validate_enterprise_group_memberships,
)
from kitsune.groups.models import GroupProfile
from kitsune.upload.utils import create_image_thumbnail, validate_avatar_size


class GroupProfileAdminForm(movenodeform_factory(GroupProfile)):  # type: ignore[misc]
    def clean_avatar(self):
        avatar = self.cleaned_data.get("avatar")
        if avatar and hasattr(avatar, "size"):
            validate_avatar_size(avatar)
        return avatar

    def clean(self):
        cleaned = super().clean()
        if error := getattr(self, "enterprise_membership_error", None):
            raise forms.ValidationError(error)
        return cleaned

    def save(self, commit=True):
        reference_node = self.cleaned_data.get("treebeard_ref_node")
        position = self.cleaned_data.get("treebeard_position")
        if (
            self.instance._state.adding
            and reference_node is not None
            and position in ("left", "right", "sorted-sibling")
        ):
            # Treebeard's temporary child placement can violate company membership.
            self.cleaned_data.pop("treebeard_ref_node")
            self.cleaned_data.pop("treebeard_position")
            self.instance = self._meta.model.objects.add_sibling(
                reference_node, pos=position, instance=self.instance
            )
            self.instance.refresh_from_db()
            return forms.ModelForm.save(self, commit=commit)
        return super().save(commit=commit)


class GroupProfileAdmin(TreeAdmin):
    form = GroupProfileAdminForm
    list_display = ["slug", "group", "visibility", "depth", "numchild"]
    list_filter = ["visibility"]
    raw_id_fields = ["leaders"]
    search_fields = ["slug", "group__name"]

    def changeform_view(self, request, object_id=None, form_url="", extra_context=None):
        if request.method == "POST":
            try:
                with lock_enterprise_hierarchy(exclusive=True):
                    return super().changeform_view(request, object_id, form_url, extra_context)
            except ValidationError as error:
                # Treebeard saves before moving; roll back before rebinding the form.
                request.enterprise_membership_error = error
        return super().changeform_view(request, object_id, form_url, extra_context)

    def move_node(self, request):
        try:
            with lock_enterprise_hierarchy(exclusive=True):
                return super().move_node(request)
        except ValidationError as error:
            message = " ".join(error.messages)
            messages.error(request, message)
            return HttpResponseBadRequest(message)

    def get_readonly_fields(self, request, obj=None):
        """Make visibility, visible_to_groups, and isolation_enabled read-only for subgroups."""
        readonly = list(super().get_readonly_fields(request, obj))

        if obj and not obj.is_root():
            if "visibility" not in readonly:
                readonly.append("visibility")
            if "visible_to_groups" not in readonly:
                readonly.append("visible_to_groups")
            if "isolation_enabled" not in readonly:
                readonly.append("isolation_enabled")

        return readonly

    def get_form(self, request, obj=None, **kwargs):
        """Add help text for visibility, visible_to_groups, and isolation_enabled fields."""
        # Since these fields can be read-only, this must happen before the super() call.
        help_texts = kwargs.setdefault("help_texts", {})

        if obj and not obj.is_root():
            help_texts["visibility"] = (
                "Visibility is inherited from the parent and cannot be changed. "
                "To change, update the root group."
            )
            help_texts["visible_to_groups"] = (
                "Groups with view-only access are inherited from the parent and cannot "
                "be changed. To change, update the root group."
            )
            help_texts["isolation_enabled"] = (
                "Isolation is controlled by the root group and cannot be changed here. "
                "To change, update the root group."
            )
        else:
            help_texts["visibility"] = (
                "Who can see this group. Children automatically inherit parent's visibility. "
                "Changing this will update all descendants in the tree."
            )
            help_texts["visible_to_groups"] = (
                "Groups with view-only access to this group (for auditing/compliance). "
                "All descendants will automatically inherit these settings."
            )
            help_texts["isolation_enabled"] = (
                "When enabled, members can only see their own hierarchy. "
                "This setting applies to the entire tree — subgroups always inherit it from here."
            )

        form = super().get_form(request, obj, **kwargs)
        form.enterprise_membership_error = getattr(request, "enterprise_membership_error", None)
        return form

    def save_model(self, request, obj, form, change):
        """Process avatar upload to resize and convert to PNG."""
        if ("avatar" in form.changed_data) and (uploaded_file := form.cleaned_data.get("avatar")):
            content = create_image_thumbnail(uploaded_file, settings.AVATAR_SIZE)
            obj.avatar.save(f"{uploaded_file.name}.png", content, save=False)

        super().save_model(request, obj, form, change)
        if "group" in form.changed_data:
            validate_enterprise_group_memberships(obj)

    def save_related(self, request, form, formsets, change):
        """
        Save related objects.

        For child nodes, skip saving "visible_to_groups" since it's inherited
        from the parent via signals. Ensure all leaders are also members.
        Ensure root nodes always have at least one leader.
        """
        # For children, prevent the form from overwriting the value of the
        # "visible_to_groups" that was inherited via the "post_save" signal.
        if form.instance and not form.instance.is_root():
            form.cleaned_data.pop("visible_to_groups", None)

        super().save_related(request, form, formsets, change)

        if form.instance.is_root() and form.instance.leaders.count() == 0:
            raise forms.ValidationError(
                "Root groups must have at least one leader. Please assign a leader before saving."
            )
        form.instance.group.user_set.add(*form.instance.leaders.all())


admin.site.register(GroupProfile, GroupProfileAdmin)
