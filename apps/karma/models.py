from django.contrib.auth.models import User, Group
from django.db import models

from sumo.models import ModelBase


class Title(ModelBase):
    """Custom karma titles."""
    name = models.CharField(max_length=100, unique=True)
    users = models.ManyToManyField(User, blank=True, help_text=(
        'Assign this title to these users.'))
    groups = models.ManyToManyField(Group, blank=True, help_text=(
        'Assign this title to these groups.'))

    def __unicode__(self):
        return self.name
