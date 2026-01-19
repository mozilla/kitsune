from django.contrib.auth.models import User
from django.db.models import Exists, OuterRef, Q
from django.db.models.functions import Length, Substr
from treebeard.mp_tree import MP_NodeManager


class GroupProfileManager(MP_NodeManager):
    def visible(self, user: User | None = None):
        """Returns a queryset of all group profiles visible to the given user."""
        from kitsune.groups.models import GroupProfile

        queryset = self.all()

        if user and user.is_superuser:
            return queryset

        public = Q(visibility=GroupProfile.Visibility.PUBLIC)

        if not (user and user.is_authenticated):
            # Anonymous users only see public groups.
            return queryset.filter(public)

        # Check if the user is a member of the group.
        member = Q(group__user=user)
        # Check if the user is a leader of the group or one of its ancestors.
        leader = Exists(
            GroupProfile.objects.filter(leaders=user).filter(
                path=Substr(OuterRef("path"), 1, Length("path"))
            )
        )
        private = Q(visibility=GroupProfile.Visibility.PRIVATE) & (member | leader)

        moderated = Q(visibility=GroupProfile.Visibility.MODERATED) & Q(
            visible_to_groups__user=user
        )

        return queryset.filter(public | private | moderated).distinct()
