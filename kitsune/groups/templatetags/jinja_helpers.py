from django.conf import settings
from django_jinja import library
from django.utils.translation import gettext as _
from markupsafe import Markup, escape

from kitsune.groups.models import GroupProfile
from kitsune.sumo.templatetags.jinja_helpers import urlparams
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
        html = '<a href="%s">%s</a>' % (escape(url), escape(group.name))
        return Markup(html)
    except GroupProfile.DoesNotExist:
        return group.name


@library.global_function
def private_message_group(group):
    """Return a link to private message the group."""
    url = urlparams(reverse("messages.new"), to_group=group)
    msg = _("Private message group members")
    return Markup(
        f'<p class="pm"><a class="sumo-button primary-button button-lg" href="{url}">{msg}</a></p>'
    )
