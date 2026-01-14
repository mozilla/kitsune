from django.conf import settings
from django.contrib.auth.models import Group, User
from django.db import models
from django.template.defaultfilters import slugify
from django.utils.translation import gettext_lazy as _lazy
from treebeard.mp_tree import MP_Node

from kitsune.sumo.models import ModelBase
from kitsune.sumo.urlresolvers import reverse
from kitsune.wiki.parser import wiki_to_html


class TreeModelBase(MP_Node, ModelBase):
    """
    Abstract base for tree-based models in Kitsune.

    Combines treebeard's MP_Node (tree operations) with Kitsune's
    ModelBase (objects_range, update methods).

    Provides:
    - Tree operations: get_parent(), get_children(), add_child(), etc.
    - ModelBase methods: objects_range(), update()

    If another app needs tree hierarchy, this can be moved to
    kitsune.sumo.models for wider reuse.
    """

    class Meta:
        abstract = True


class GroupProfile(TreeModelBase):
    """Profile model for groups with hierarchy support."""

    path = models.CharField(max_length=255, unique=True, null=True, blank=True)
    depth = models.PositiveIntegerField(null=True, blank=True)
    numchild = models.PositiveIntegerField(default=0, null=True, blank=True)

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
