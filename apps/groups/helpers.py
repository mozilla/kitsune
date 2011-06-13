from django.conf import settings

from jingo import register


@register.function
def group_avatar(group_profile):
    """Return a URL to the group's avatar."""
    if group_profile.avatar:
        return group_profile.avatar.url
    else:
        return settings.DEFAULT_AVATAR
