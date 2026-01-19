from django.conf import settings
from django.contrib.auth.models import Group, User
from django.db import models
from django.db.models import Exists, OuterRef, Value
from django.db.models.functions import Length, Substr
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
        help_text="Who can see this group",
    )
    visible_to_groups = models.ManyToManyField(
        Group,
        related_name="visible_group_profiles",
        blank=True,
        help_text="Groups that can see this group when visibility is MODERATED",
    )

    objects = GroupProfileManager()

    class Meta:
        ordering = ["slug"]

    def __str__(self):
        return str(self.group)

    def get_absolute_url(self):
        return reverse("groups.profile", args=[self.slug])

    def save(self, *args, **kwargs):
        """Set slug on first save and parse information to html."""
        if not self.slug:
            self.slug = slugify(self.group.name)

        self.information_html = wiki_to_html(self.information)

        super().save(*args, **kwargs)

    def can_moderate_group(self, user):
        """
        Check if user can moderate this group (manage members and leaders).

        Direct leaders have full control. If this group has no leaders,
        delegate to nearest ancestor with leaders.
        """
        if not (user and user.is_authenticated):
            return False

        if user.is_superuser:
            return True

        # Is the user a leader of this group, if it has leaders,
        # or its nearest ancestor group with leaders, if one exists.
        return bool(
            GroupProfile.objects.filter(
                leaders__isnull=False,
                path=Substr(Value(self.path), 1, Length("path")),
            )
            .order_by("-path")
            .annotate(
                is_leader=Exists(
                    GroupProfile.objects.filter(
                        pk=OuterRef("pk"),
                        leaders=user,
                    )
                )
            )
            .values_list("is_leader", flat=True)
            .first()
        )

    def can_edit(self, user):
        """Check if user can edit this group profile."""
        return self.can_moderate_group(user)

    def can_view(self, user):
        """Check if user can view this group based on visibility setting."""
        # PUBLIC groups are visible to everyone
        if self.visibility == self.Visibility.PUBLIC:
            return True

        # Non-authenticated users can only see PUBLIC groups
        if not (user and user.is_authenticated):
            return False

        # Superusers can see everything
        if user.is_superuser:
            return True

        # Check based on visibility level
        match self.visibility:
            case self.Visibility.MODERATED:
                # Visible to members of specified groups
                return self.visible_to_groups.filter(user=user).exists()
            case self.Visibility.PRIVATE:
                # Members can see their own group
                if self.group.user_set.filter(pk=user.pk).exists():
                    return True
                # Moderators (including delegated) can see private groups
                return self.can_moderate_group(user)
            case _:
                return False

    def get_visible_children(self, user):
        """Get child groups visible to this user."""
        children = self.get_children()
        return GroupProfile.objects.filter(pk__in=children).visible(user)
