from datetime import datetime

from django.contrib.auth.models import User, Group
from django.core.cache import cache
from django.db import models

from caching.base import CachingManager

from kitsune.sumo.models import ModelBase


class TitleManager(CachingManager):
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

    def set_top10_contributors(self, users):
        return self.set_auto_title('Top 10 Contributor', users)

    def set_top25_contributors(self, users):
        return self.set_auto_title('Top 25 Contributor', users)


class Title(ModelBase):
    """Karma titles."""
    name = models.CharField(max_length=100, unique=True)
    users = models.ManyToManyField(User, blank=True, help_text=(
        'Assign this title to these users.'))
    groups = models.ManyToManyField(Group, blank=True, help_text=(
        'Assign this title to these groups.'))

    # is_auto is True for titles that are set automatically by the system
    # (Top 10 Contributor, Top 25 Contributor, Rising Star, etc.).
    is_auto = models.BooleanField(default=False)

    objects = TitleManager()

    def __unicode__(self):
        return self.name

    class Meta:
        # Karma dashboard permission isn't exactly related to Titles, but
        # this is the only karma model to hang a permission on.
        permissions = (('view_dashboard', 'Can access karma dashboard'), )


class Points(ModelBase):
    """A Model to override the default karma points."""
    action = models.CharField(
        max_length=100,
        unique=True,
        choices=(
            ('answer', 'Answer'),
            ('first-answer', 'First Answer'),
            ('helpful-answer', 'Helpful Answer Vote'),
            ('nothelpful-answer', 'Not Helpful Answer Vote'),
            ('solution', 'Solution'),
        ))
    points = models.IntegerField()
    updated = models.DateTimeField()

    cache_key = u'karma:points:%s'

    def __unicode__(self):
        return self.action

    class Meta:
        verbose_name_plural = 'Points'

    def clear_cache(self):
        cache.delete(self.cache_key % self.action)

    @classmethod
    def get_points(cls, action):
        """Return points value for the passed action.

        :args action: A KarmaAction class or instance.

        Checks in db first and falls back to action.default_points.
        """
        # cache-machine won't cache queries that raise DoesNotExist.
        # So adding another layer of caching here.
        cache_key = cls.cache_key % action.action_type
        pts = cache.get(cache_key)
        if pts is None:
            try:
                pts = cls.objects.get(action=action.action_type).points
            except cls.DoesNotExist:
                pts = action.default_points
            cache.add(cache_key, pts)
        return pts

    def save(self, *args, **kwargs):
        """Override save method to set updated and clean out cache."""
        self.updated = datetime.now()
        super(Points, self).save(*args, **kwargs)

        self.clear_cache()
