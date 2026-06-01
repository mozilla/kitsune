from django.conf import settings
from django.utils.translation import gettext as _
from django_jinja import library
from markupsafe import Markup, escape

from kitsune.groups.models import GroupProfile
from kitsune.sumo.urlresolvers import reverse
from kitsune.sumo.utils import webpack_static


@library.global_function
def group_avatar(group_profile):
    """Return a URL to the group's avatar."""
    if group_profile.avatar:
        return group_profile.avatar.url
    else:
        return webpack_static(settings.DEFAULT_AVATAR)


@library.global_function
def group_link(group):
    try:
        profile = GroupProfile.objects.get(group=group)
        url = reverse("groups.profile", args=[profile.slug])
        html = '<a href="{}">{}</a>'.format(escape(url), escape(group.name))
        return Markup(html)
    except GroupProfile.DoesNotExist:
        return group.name


@library.global_function
def group_breadcrumbs(group_profile, include_self=True):
    """Breadcrumb chain for a group: ``Groups > ancestors > [self]``.

    Returns a list of (url, label) tuples, all linked. Callers append their
    own trailing (None, leaf) crumb. Pass include_self=False on a page where
    the group itself is the current (unlinked) leaf.
    """
    crumbs = [(reverse("groups.list"), _("Groups"))]
    for ancestor in group_profile.get_ancestors():
        crumbs.append((reverse("groups.profile", args=[ancestor.slug]), ancestor.group.name))
    if include_self:
        crumbs.append(
            (reverse("groups.profile", args=[group_profile.slug]), group_profile.group.name)
        )
    return crumbs
