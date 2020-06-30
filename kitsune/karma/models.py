from django.contrib.auth.models import User, Group
from django.db import models

from kitsune.sumo.models import ModelBase


class TitleManager(models.Manager):
    """A custom manager for titles that adds some helper methods
    for dealing with setting automatic titles."""

    def set_auto_title(self, name, users):
        """Set the title of given name to given users."""
        try:
            # Get the title and current users
            title = self.get(name=name)
            current = set(title.users.all())
            users = set(users)
            # Remove users that lost the title, and add the new ones
            title.users.remove(*[u for u in current - users])
            title.users.add(*[u for u in users - current])
        except Title.DoesNotExist:
            # Create the title and add the users
            title = Title(name=name, is_auto=True)
            title.save()
            title.users.add(*users)

    def set_top10_contributors(self, user_ids):
        users = User.objects.filter(id__in=user_ids)
        return self.set_auto_title("Top 10 Contributor", users)

    def set_top25_contributors(self, user_ids):
        users = User.objects.filter(id__in=user_ids)
        return self.set_auto_title("Top 25 Contributor", users)


class Title(ModelBase):
    """Karma titles."""

    name = models.CharField(max_length=100, unique=True)
    users = models.ManyToManyField(
        User, blank=True, help_text=("Assign this title to these users.")
    )
    groups = models.ManyToManyField(
        Group, blank=True, help_text=("Assign this title to these groups.")
    )

    # is_auto is True for titles that are set automatically by the system
    # (Top 10 Contributor, Top 25 Contributor, Rising Star, etc.).
    is_auto = models.BooleanField(default=False)

    objects = TitleManager()

    def __str__(self):
        return self.name
