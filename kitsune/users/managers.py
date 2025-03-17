from django.contrib.auth.models import UserManager
from django.db import models


class RegularUserManager(UserManager):
    """Manager that excludes users with system account profiles."""

    def get_queryset(self):
        from django.contrib.auth.models import User

        from kitsune.users.models import Profile

        if hasattr(User, "all_users"):
            qs = User.all_users.get_queryset()
        else:
            qs = super(UserManager, self).get_queryset()

        return qs.exclude(profile__account_type=Profile.AccountType.SYSTEM)


class RegularProfileManager(models.Manager):
    """Manager that excludes system account profiles."""

    def get_queryset(self):
        from kitsune.users.models import Profile

        return super().get_queryset().exclude(account_type=Profile.AccountType.SYSTEM)


class AllProfilesManager(models.Manager):
    """Manager that includes all profiles, including system accounts."""

    pass
