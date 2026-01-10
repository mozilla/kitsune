from django.conf import settings
from django.contrib.auth.models import Group, User
from django.db import models
from django.db.models import Q
from django.template.defaultfilters import slugify
from django.utils.translation import gettext_lazy as _lazy

from kitsune.sumo.models import ModelBase
from kitsune.sumo.urlresolvers import reverse
from kitsune.wiki.parser import wiki_to_html


class GroupProfileManager(models.Manager):
    def visible(self, user=None):
        """Returns a queryset of all group profiles visible to the given user."""
        return GroupProfile.filter_by_visibility(self.all(), user)


class GroupProfile(ModelBase):
    """Profile model for groups."""

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
    is_private = models.BooleanField(
        default=False,
        help_text="Only group members, group leaders, and superusers, can view a private group.",
    )

    objects = GroupProfileManager()

    class Meta:
        ordering = ["slug"]

    @classmethod
    def filter_by_visibility(cls, queryset, user=None):
        """
        Given a Group or GroupProfile queryset, and a user, returns a new queryset
        filtered to the groups or group profiles visible to the given user. If the
        given user is a superuser, the queryset is returned unmodified. If the given
        queryset is not for groups or group profiles, a TypeError is raised.
        """
        if queryset.model not in (Group, GroupProfile):
            raise TypeError(
                f"The queryset's model ({queryset.model}) is not Group or GroupProfile."
            )

        if user and user.is_superuser:
            return queryset

        public_groups = Q(profile__isnull=True) | Q(profile__is_private=False)

        if not (user and user.is_authenticated):
            # Anonymous users only see public groups.
            if queryset.model is Group:
                return queryset.filter(public_groups)
            return queryset.filter(is_private=False)

        # Private group members and leaders can also see their own groups.
        if queryset.model is Group:
            return queryset.filter(
                public_groups | Q(profile__leaders=user) | Q(user=user)
            ).distinct()

        return queryset.filter(
            Q(is_private=False) | Q(leaders=user) | Q(group__user=user)
        ).distinct()

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
