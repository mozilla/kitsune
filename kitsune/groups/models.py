from django.conf import settings
from django.contrib.auth.models import Group, User
from django.db import models
from django.db.models import Q
from django.template.defaultfilters import slugify
from django.utils.translation import gettext_lazy as _lazy
from treebeard.mp_tree import MP_Node

from kitsune.groups.managers import GroupProfileManager
from kitsune.sumo.models import ModelBase
from kitsune.sumo.urlresolvers import reverse
from kitsune.wiki.parser import wiki_to_html


class TreeModelBase(MP_Node, ModelBase):
    """
    Abstract base for tree-based models in Kitsune.

    Combines treebeard's MP_Node with ModelBase

    Provides:
    - Tree operations: get_parent(), get_children(), add_child(), etc.
    - ModelBase methods: objects_range(), update()
    """

    class Meta:
        abstract = True


class GroupProfile(TreeModelBase):
    """Profile model for groups with hierarchy support."""

    class Visibility(models.TextChoices):
        PRIVATE = "private", "Private - members only"
        PUBLIC = "public", "Public - visible to all"
        MODERATED = "moderated", "Moderated - visible to specific groups"

    slug = models.SlugField(unique=True, editable=False, blank=False, null=False, max_length=80)
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name="profile")
    leaders = models.ManyToManyField(User)
    information = models.TextField(help_text="Use Wiki Syntax")
    information_html = models.TextField(editable=False)
    avatar = models.ImageField(
        upload_to=settings.GROUP_AVATAR_PATH,
        null=True,
        blank=True,
        verbose_name=_lazy("Avatar"),
        max_length=settings.MAX_FILEPATH_LENGTH,
    )
    visibility = models.CharField(
        max_length=20,
        choices=Visibility.choices,
        default=Visibility.PUBLIC,
        help_text="Who can see this group. Children automatically inherit parent's visibility.",
    )
    isolation_enabled = models.BooleanField(
        default=True,
        help_text="Enable sibling isolation for PRIVATE/MODERATED groups. "
                  "When enabled, members can only see their hierarchy (ancestors + descendants), not siblings.",
    )
    visible_to_groups = models.ManyToManyField(
        Group,
        related_name="visible_group_profiles",
        blank=True,
        help_text="Groups with view-only access to this group (for auditing/compliance).",
    )

    objects = GroupProfileManager()

    class Meta:
        ordering = ["slug"]

    def __str__(self):
        return str(self.group)

    def get_absolute_url(self):
        return reverse("groups.profile", args=[self.slug])

    def save(self, *args, **kwargs):
        """Set slug on first save, parse information to html, and inherit parent visibility."""
        if not self.slug:
            self.slug = slugify(self.group.name)

        update_fields = kwargs.get('update_fields')
        if not self.pk or update_fields is None or 'information' in update_fields:
            self.information_html = wiki_to_html(self.information)

        if len(self.path) > self.steplen:
            parent = self.get_parent()
            if parent:
                self.visibility = parent.visibility

        super().save(*args, **kwargs)

    def update_visibility(self, new_visibility, propagate=True):
        """
        Update visibility for this group and optionally all descendants.

        Args:
            new_visibility: New visibility level
            propagate: If True, update all descendants too (default: True)
        """
        self.visibility = new_visibility
        self.save(update_fields=['visibility'])

        if propagate:
            self.get_descendants().update(visibility=new_visibility)

    def can_moderate_group(self, user):
        """
        Check if user can moderate this group.

        Moderation rules:
        - Root moderators: Can moderate entire tree
        - Non-root moderators: Can moderate ONLY their specific group (not descendants)
        - Inheritance: If no local moderators, inherits from ROOT only (not parent)

        Returns True if user can add/remove members and edit group settings.
        """
        if not (user and user.is_authenticated):
            return False

        if user.is_superuser:
            return True

        if self.leaders.filter(pk=user.pk).exists():
            return True

        if not self.is_root():
            root = self.get_root()
            if root.leaders.filter(pk=user.pk).exists():
                return True

        return False

    def can_edit(self, user):
        """
        Check if user can edit this group's settings (info, avatar).

        Root moderators can edit entire tree.
        Non-root moderators can edit only their specific group.
        """
        return self.can_moderate_group(user)

    def can_delete_subgroup(self, user, subgroup):
        """
        Check if user can delete a subgroup.

        Only root moderators can delete subgroups.
        """
        if not (user and user.is_authenticated):
            return False

        if user.is_superuser:
            return True

        root = self.get_root()
        return root.leaders.filter(pk=user.pk).exists()

    def can_view(self, user):
        """Check if user can view this group based on visibility and isolation settings."""
        return self.__class__.objects.visible(user).filter(pk=self.pk).exists()

    def get_visible_children(self, user):
        """Return child groups visible to this user."""
        children = self.get_children()

        if self.can_moderate_group(user):
            return children

        if not (user and user.is_authenticated):
            return children.filter(visibility=self.Visibility.PUBLIC)

        is_parent_member = self.group.user_set.filter(pk=user.pk).exists()

        filters = Q(visibility=self.Visibility.PUBLIC)
        if is_parent_member:
            filters |= Q(visibility=self.Visibility.PRIVATE)

        filters |= Q(
            visibility=self.Visibility.MODERATED,
            visible_to_groups__user=user
        )

        return children.filter(filters).distinct()
