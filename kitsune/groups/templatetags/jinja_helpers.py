from django.conf import settings

import jinja2
from django_jinja import library

from kitsune.groups.models import GroupProfile
from kitsune.sumo.urlresolvers import reverse


@library.global_function
def group_avatar(group_profile):
    """Return a URL to the group's avatar."""
    if group_profile.avatar:
        return group_profile.avatar.url
    else:
        return settings.STATIC_URL + settings.DEFAULT_AVATAR


@library.global_function
def group_link(group):
    try:
        profile = GroupProfile.objects.get(group=group)
        url = reverse('groups.profile', args=[profile.slug])
        html = '<a href="%s">%s</a>' % (jinja2.escape(url), jinja2.escape(group.name))
        return jinja2.Markup(html)
    except GroupProfile.DoesNotExist:
        return group.name
