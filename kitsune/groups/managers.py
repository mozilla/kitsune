from django.contrib.auth.models import User
from django.db.models import Exists, OuterRef, Q
from django.db.models.functions import Length, Substr
from treebeard.mp_tree import MP_NodeManager


class GroupProfileManager(MP_NodeManager):
    def visible(self, user: User | None = None):
        """
        Returns a queryset of all group profiles visible to the given user.

        Visibility rules with isolation enabled (default):

        PUBLIC: Always visible to everyone

        PRIVATE/MODERATED with isolation:
        - Root moderators: View entire tree
        - Root members: View entire tree
        - Node members: View ancestors + own group + descendants
        - Node moderators: View ancestors + own group + descendants
        - visible_to_groups: View-only cross-hierarchy access

        Example:
          Root (member: Alice, Bob; moderator: Mike)
          ├── SubA (member: Alice, Charlie)
          └── SubB (member: Bob)

          Alice: Sees entire tree (root member)
          Bob: Sees entire tree (root member)
          Charlie: Sees Root + SubA only (node member, sibling isolation)
          Mike: Sees entire tree (root moderator)
        """

        queryset = self.all()

        if user and user.is_superuser:
            return queryset

        public = Q(visibility=self.model.Visibility.PUBLIC)

        # Anonymous users see all public groups
        if not (user and user.is_authenticated):
            return queryset.filter(public)

        private = Q(visibility=self.model.Visibility.PRIVATE)
        moderated = Q(visibility=self.model.Visibility.MODERATED)
        member_or_leader = Q(group__user=user) | Q(leaders=user)

        # Members/leaders of groups can see the entire tree below their groups.
        # This condition is true if the group under consideration is a descendant
        # of a group in which the user is a member or leader.
        descendant = Exists(
            self.model.objects.filter(
                member_or_leader,
                path=Substr(OuterRef("path"), 1, Length("path")),
            )
        )
        # Members/leaders of groups can see the ancestors above their groups.
        # This condition is true if the group under consideration is an ancestor
        # of a group in which the user is a member or leader.
        ancestor = Exists(
            self.model.objects.filter(
                member_or_leader,
                path__startswith=OuterRef("path"),
            )
        )

        root_path_expr = Substr(OuterRef("path"), 1, self.model.steplen)
        # This condition is true if the root of the group under consideration is not isolated.
        root_not_isolated = Exists(
            self.model.objects.filter(
                path=root_path_expr,
                isolation_enabled=False,
            )
        )
        # This condition is true if the user is a member or leader of at least one group
        # within the tree starting at the root of the group under consideration.
        user_within_tree = Exists(
            self.model.objects.filter(
                member_or_leader,
                path__startswith=root_path_expr,
            )
        )

        not_isolated = root_not_isolated & user_within_tree

        private_moderated = (private | moderated) & (ancestor | descendant | not_isolated)

        cross_hierarchy = moderated & Q(visible_to_groups__user=user)

        return queryset.filter(public | private_moderated | cross_hierarchy).distinct()
