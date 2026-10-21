from django.conf import settings
from django.contrib.auth.models import Group, User
from django.db.models import Exists, Max, OuterRef, Q
from django.db.models.functions import Length, Substr
from treebeard.mp_tree import MP_NodeManager, MP_NodeQuerySet

from kitsune.groups.membership import (
    guard_enterprise_group_move,
    lock_enterprise_hierarchy,
    validate_enterprise_group_memberships,
)


class GroupProfileQuerySet(MP_NodeQuerySet):
    def descendants(self):
        """Every profile below these ones."""
        at_or_above = self.filter(path=Substr(OuterRef("path"), 1, Length("path")))
        return (
            self.model.objects.using(self.db)
            .filter(Exists(at_or_above))
            .exclude(pk__in=self.values("pk"))
        )

    def subgroup_groups(self):
        """
        The Groups of the profiles below these ones, which deleting these deletes too.

        Leaves out the Groups of these profiles, and any Group that also has a profile
        outside this subtree: only its profiles in the subtree get deleted. Each Group
        has a "depth", its deepest profile's depth, for deleting deepest first.
        """
        below = self.descendants()
        elsewhere = (
            self.model.objects.using(self.db)
            .filter(group=OuterRef("pk"))
            .exclude(pk__in=below.values("pk"))
            .exclude(pk__in=self.values("pk"))
        )
        return (
            Group.objects.using(self.db)
            .filter(profile__in=below)
            .exclude(pk__in=self.values("group_id"))
            .exclude(Exists(elsewhere))
            .annotate(depth=Max("profile__depth"))
        )

    def delete(self, *args, **kwargs):
        # Treebeard reads paths in one query and deletes by path in another, so a
        # move in between could make it delete the wrong subtree.
        with lock_enterprise_hierarchy(using=self.db, exclusive=True):
            # Deepest first, so each subgroup's delete handlers still see the tree above it.
            for group in list(self.subgroup_groups().order_by("-depth")):
                group.delete(using=self.db)
            return super().delete(*args, **kwargs)

    delete.alters_data = True  # type: ignore[attr-defined]
    delete.queryset_only = True  # type: ignore[attr-defined]


class GroupProfileManager(MP_NodeManager):
    def get_queryset(self):
        return GroupProfileQuerySet(self.model, using=self._db).order_by("path")

    def add_root(self, create_kwargs=None, *, instance=None):
        with lock_enterprise_hierarchy(using=self.db, exclusive=True):
            node = super().add_root(create_kwargs, instance=instance)
            validate_enterprise_group_memberships(node, using=self.db)
            return node

    def add_child(self, target, create_kwargs=None, *, instance=None):
        with lock_enterprise_hierarchy(using=self.db, exclusive=True):
            target.refresh_from_db(using=self.db)
            node = super().add_child(target, create_kwargs, instance=instance)
            validate_enterprise_group_memberships(node, using=self.db)
            return node

    def add_sibling(self, target, pos=None, create_kwargs=None, *, instance=None):
        with lock_enterprise_hierarchy(using=self.db, exclusive=True):
            target.refresh_from_db(using=self.db)
            node = super().add_sibling(target, pos, create_kwargs, instance=instance)
            validate_enterprise_group_memberships(node, using=self.db)
            return node

    def move(self, node, target, pos=None):
        with guard_enterprise_group_move(node, target, using=self.db):
            return super().move(node, target, pos)

    def org_roots(self):
        """All GroupProfiles whose group is configured as a support organization."""
        return self.filter(group__support_organizations__isnull=False).distinct()

    def containing_groups(self, groups):
        """These groups and every group above them."""
        return self.filter(
            Exists(self.model.objects.filter(path__startswith=OuterRef("path"), group__in=groups))
        )

    def containing(self, user):
        """Groups containing the user directly or through a subgroup, excluding leadership."""
        if not (user and user.is_authenticated):
            return self.none()
        return self.filter(
            Exists(self.model.objects.filter(path__startswith=OuterRef("path"), group__user=user))
        )

    def enterprise_companies(self, user):
        if not (user and user.is_authenticated):
            return self.none()
        root = self.filter(slug=settings.ENTERPRISE_GROUP_SLUG, depth=1).first()
        if root is None:
            return self.none()
        return self.containing(user).filter(depth=2, path__startswith=root.path)

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
