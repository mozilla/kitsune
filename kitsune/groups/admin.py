from django.conf import settings
from django.contrib import admin
from treebeard.admin import TreeAdmin
from treebeard.forms import movenodeform_factory

from kitsune.groups.models import GroupProfile
from kitsune.upload.tasks import create_image_thumbnail


class GroupProfileAdmin(TreeAdmin):
    form = movenodeform_factory(GroupProfile)
    list_display = ["slug", "group", "visibility", "depth", "numchild"]
    list_filter = ["visibility"]
    raw_id_fields = ["leaders"]
    search_fields = ["slug", "group__name"]

    def get_readonly_fields(self, request, obj=None):
        """Make visibility and visible_to_groups read-only for subgroups (non-root nodes)."""
        readonly = list(super().get_readonly_fields(request, obj))

        if obj and not obj.is_root():
            if "visibility" not in readonly:
                readonly.append("visibility")
            if "visible_to_groups" not in readonly:
                readonly.append("visible_to_groups")

        return readonly

    def get_form(self, request, obj=None, **kwargs):
        """Add help text for visibility and visible_to_groups fields based on node type."""
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
        else:
            help_texts["visibility"] = (
                "Who can see this group. Children automatically inherit parent's visibility. "
                "Changing this will update all descendants in the tree."
            )
            help_texts["visible_to_groups"] = (
                "Groups with view-only access to this group (for auditing/compliance). "
                "All descendants will automatically inherit these settings."
            )

        return super().get_form(request, obj, **kwargs)

    def save_model(self, request, obj, form, change):
        """Process avatar upload to resize and convert to PNG."""
        if ("avatar" in form.changed_data) and (uploaded_file := form.cleaned_data.get("avatar")):
            content = create_image_thumbnail(uploaded_file, settings.AVATAR_SIZE)
            obj.avatar.save(f"{uploaded_file.name}.png", content, save=False)

        super().save_model(request, obj, form, change)

    def save_related(self, request, form, formsets, change):
        """
        Save related objects.

        For child nodes, skip saving "visible_to_groups" since it's inherited
        from the parent via signals. Ensure all leaders are also members.
        """
        # For children, prevent the form from overwriting the value of the
        # "visible_to_groups" that was inherited via the "post_save" signal.
        if form.instance and not form.instance.is_root():
            form.cleaned_data.pop("visible_to_groups", None)

        super().save_related(request, form, formsets, change)

        for leader in form.instance.leaders.all():
            if not leader.groups.filter(pk=form.instance.group.pk).exists():
                leader.groups.add(form.instance.group)


admin.site.register(GroupProfile, GroupProfileAdmin)
