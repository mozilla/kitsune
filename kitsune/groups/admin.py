from django.contrib import admin
from treebeard.admin import TreeAdmin
from treebeard.forms import movenodeform_factory

from kitsune.groups.models import GroupProfile


class GroupProfileAdmin(TreeAdmin):
    form = movenodeform_factory(GroupProfile)
    list_display = ["slug", "group", "visibility", "depth", "numchild"]
    list_filter = ["visibility"]
    raw_id_fields = ["leaders"]
    search_fields = ["slug", "group__name"]

    def get_readonly_fields(self, request, obj=None):
        """Make visibility read-only for subgroups (non-root nodes)."""
        readonly = list(super().get_readonly_fields(request, obj))

        if obj and not obj.is_root():
            if "visibility" not in readonly:
                readonly.append("visibility")

        return readonly

    def get_form(self, request, obj=None, **kwargs):
        """Add help text for visibility field based on node type."""
        form = super().get_form(request, obj, **kwargs)

        if "visibility" in form.base_fields:
            if obj and not obj.is_root():
                form.base_fields["visibility"].help_text = (
                    "Visibility is inherited from parent group and cannot be changed. "
                    f"This group inherits '{obj.get_parent().visibility}' from its parent. "
                    "To change visibility, update the root group."
                )
            else:
                form.base_fields["visibility"].help_text = (
                    "Who can see this group. Children automatically inherit parent's visibility. "
                    "Changing this will update all descendants in the tree."
                )

        return form

    def save_related(self, request, form, formsets, change):
        """Ensure all leaders are also members of the group."""
        super().save_related(request, form, formsets, change)
        for leader in form.instance.leaders.all():
            if not leader.groups.filter(pk=form.instance.group.pk).exists():
                leader.groups.add(form.instance.group)


admin.site.register(GroupProfile, GroupProfileAdmin)
