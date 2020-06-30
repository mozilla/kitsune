from django.conf import settings
from django.contrib.auth.models import Group, User
from django.db import models
from django.template.defaultfilters import slugify
from django.utils.translation import ugettext_lazy as _lazy

from kitsune.sumo.models import ModelBase
from kitsune.sumo.urlresolvers import reverse
from kitsune.wiki.parser import wiki_to_html


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

        super(GroupProfile, self).save(*args, **kwargs)
