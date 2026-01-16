from django.conf import settings
from django.contrib.auth.models import Group, User
from django.db import models
from django.db.models import Exists, OuterRef, Q, QuerySet
from django.db.models.functions import Length, Substr
from django.template.defaultfilters import slugify
from django.utils.translation import gettext_lazy as _lazy
from treebeard.mp_tree import MP_Node

from kitsune.sumo.models import ModelBase
from kitsune.sumo.urlresolvers import reverse
from kitsune.wiki.parser import wiki_to_html


class GroupProfileManager(models.Manager):
    def visible(self, user=None):
        """Returns a queryset of all group profiles visible to the given user."""
        return GroupProfile.filter_by_visible(self.all(), user)


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

    @classmethod
    def filter_by_visible(
        cls, queryset: QuerySet[Group] | QuerySet["GroupProfile"], user: User | None = None
    ) -> QuerySet[Group] | QuerySet["GroupProfile"]:
        """
        Given a Group or GroupProfile queryset, and a user, returns a new queryset
        filtered to the groups or group profiles visible to the given user. If the
        given user is a superuser, the queryset is returned unmodified.
        """
        if user and user.is_superuser:
            return queryset

        if queryset.model is Group:
            prefix = "profile__"
            user_prefix = ""
            # Groups without a profile are considered public.
            public = Q(profile__isnull=True) | Q(profile__visibility=cls.Visibility.PUBLIC)
        else:
            prefix = ""
            user_prefix = "group__"
            public = Q(visibility=cls.Visibility.PUBLIC)

        if not (user and user.is_authenticated):
            # Anonymous users only see public groups.
            return queryset.filter(public)

        # Check if the user is a member of the group.
        member = Q(**{f"{user_prefix}user": user})
        # Check if the user is a leader of the group or one of its ancestors.
        leader = Exists(
            cls.objects.filter(leaders=user).filter(
                path=Substr(OuterRef(f"{prefix}path"), 1, Length("path"))
            )
        )
        private = Q(**{f"{prefix}visibility": cls.Visibility.PRIVATE}) & (member | leader)

        moderated = Q(**{f"{prefix}visibility": cls.Visibility.MODERATED}) & Q(
            **{f"{prefix}visible_to_groups__in": user.groups.all()}
        )

        return queryset.filter(public | private | moderated).distinct()

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

    def is_governing_leader(self, user):
        """
        Check if user can lead this group.

        If this group has no leaders, delegate to nearest ancestor with leaders.
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
                path=Substr(self.path, 1, Length("path")),
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
        """Check if user can edit this group."""
        return self.is_governing_leader(user)

    def can_manage_members(self, user):
        """Check if user can add/remove members."""
        return self.is_governing_leader(user)

    def can_manage_leaders(self, user):
        """Check if user can add/remove leaders."""
        return (
            user
            and user.is_authenticated
            and (user.is_superuser or self.leaders.filter(pk=user.pk).exists())
        )

    def can_view(self, user):
        """Check if user can view this group based on visibility setting."""
        if self.visibility == self.Visibility.PUBLIC:
            return True

        if not (user and user.is_authenticated):
            return False

        if user.is_superuser:
            return True

        if self.visibility == self.Visibility.MODERATED:
            return self.visible_to_groups.filter(pk__in=user.groups.all()).exists()

        # From here on, we're dealing with groups with PRIVATE visibility.

        if self.group.user_set.filter(pk=user.pk).exists():
            # Group members can see their own groups.
            return True

        # Other than members, only governing leaders can see private groups.
        return self.is_governing_leader(user)

    def get_visible_children(self, user):
        """Get child groups visible to this user."""
        return self.filter_by_visible(self.get_children(), user)
