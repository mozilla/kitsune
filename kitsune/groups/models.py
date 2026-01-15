from django.conf import settings
from django.contrib.auth.models import Group, User
from django.db import models
from django.db.models import Q
from django.template.defaultfilters import slugify
from django.utils.translation import gettext_lazy as _lazy
from treebeard.mp_tree import MP_Node

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

    def can_edit(self, user):
        """Check if user can edit this group.

        If no leaders exist, delegates to parent leaders.
        """
        if user.is_superuser or self.leaders.filter(pk=user.pk).exists():
            return True
        if not self.leaders.exists():
            parent = self.get_parent()
            if parent:
                return parent.can_edit(user)
        return False

    def can_manage_members(self, user):
        """Check if user can add/remove members."""
        return self.can_edit(user)

    def can_manage_leaders(self, user):
        """Check if user can add/remove leaders."""
        return user.is_superuser or self.leaders.filter(pk=user.pk).exists()

    def can_view(self, user):
        """Check if user can view this group based on visibility setting."""
        if user.is_superuser:
            return True

        match self.visibility:
            case self.Visibility.PRIVATE:
                return self.group.user_set.filter(pk=user.pk).exists()
            case self.Visibility.PUBLIC:
                return True
            case self.Visibility.MODERATED:
                return self.visible_to_groups.filter(pk__in=user.groups.all()).exists()

    def get_visible_children(self, user):
        """Get child groups visible to this user."""
        if user.is_superuser:
            return self.get_children()

        public = Q(visibility=self.Visibility.PUBLIC)
        private = Q(visibility=self.Visibility.PRIVATE) & Q(group__user_set__pk=user.pk)
        moderated = Q(visibility=self.Visibility.MODERATED) & Q(visible_to_groups__in=user.groups.all())
        return self.get_children().filter(public | private | moderated)
