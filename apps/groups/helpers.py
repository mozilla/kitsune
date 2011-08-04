from django.conf import settings

from jingo import register
from jinja2 import Markup, escape

from groups.models import GroupProfile
from sumo.urlresolvers import reverse


@register.function
def group_avatar(group_profile):
    """Return a URL to the group's avatar."""
    if group_profile.avatar:
        return group_profile.avatar.url
    else:
        return settings.DEFAULT_AVATAR


@register.function
def group_link(group):
    try:
        profile = GroupProfile.objects.get(group=group)
        url = reverse('groups.profile', args=[profile.slug])
        html = '<a href="%s">%s</a>' % (escape(url), escape(group.name))
        return Markup(html)
    except GroupProfile.DoesNotExist:
        return group.name
