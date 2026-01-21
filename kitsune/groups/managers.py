from django.contrib.auth.models import User
from django.db.models import Q
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

        # Anonymous users see all public groups
        if not (user and user.is_authenticated):
            return queryset.filter(visibility=self.model.Visibility.PUBLIC)

        steplen = self.model.steplen
        all_user_profiles = self.filter(Q(group__user=user) | Q(leaders=user)).distinct()

        if not all_user_profiles:
            return queryset.filter(visibility=self.model.Visibility.PUBLIC)

        root_paths = {p.path[:steplen] for p in all_user_profiles}

        root_nodes = self.filter(path__in=root_paths).prefetch_related(
            "group__user_set", "leaders"
        )

        full_access_paths = set()
        for root in root_nodes:
            is_root_member = root.group.user_set.filter(pk=user.pk).exists()
            is_root_moderator = root.leaders.filter(pk=user.pk).exists()
            if is_root_member or is_root_moderator or not root.isolation_enabled:
                full_access_paths.add(root.path)

        visibility_q = Q(pk__in=[])

        for path in full_access_paths:
            visibility_q |= Q(path__startswith=path)

        for profile in all_user_profiles:
            root_path = profile.path[:steplen]
            if root_path not in full_access_paths:
                ancestor_paths = [
                    profile.path[:i] for i in range(steplen, len(profile.path), steplen)
                ]

                visibility_q |= Q(path__in=ancestor_paths)
                visibility_q |= Q(path__startswith=profile.path)

        public = Q(visibility=self.model.Visibility.PUBLIC)
        private_moderated = (
            Q(visibility__in=[self.model.Visibility.PRIVATE, self.model.Visibility.MODERATED])
            & visibility_q
        )
        cross_hierarchy = Q(visible_to_groups__user=user)
        return queryset.filter(public | private_moderated | cross_hierarchy).distinct()
