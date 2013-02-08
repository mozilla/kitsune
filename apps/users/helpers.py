from django.conf import settings
from django.utils.html import strip_tags

from jinja2 import escape, Markup
from jingo import register
from tower import ugettext as _

from sumo.helpers import urlparams
from sumo.urlresolvers import reverse
from users.models import Profile


@register.function
def profile_url(user, edit=False):
    """Return a URL to the user's profile."""
    if edit:
        return reverse('users.edit_profile', args=[])
    return reverse('users.profile', args=[user.pk])


@register.function
def profile_avatar(user):
    """Return a URL to the user's avatar."""
    try:  # This is mostly for tests.
        profile = user.get_profile()
    except (Profile.DoesNotExist, AttributeError):
        return settings.DEFAULT_AVATAR
    return (profile.avatar.url if profile and profile.avatar else
            settings.DEFAULT_AVATAR)


@register.function
def display_name(user):
    """Return a display name if set, else the username."""
    try:  # Also mostly for tests.
        profile = user.get_profile()
    except Profile.DoesNotExist:
        return strip_tags(user.username)
    return strip_tags(profile.name if profile and profile.name else user.username)


@register.filter
def public_email(email):
    """Email address -> publicly displayable email."""
    return Markup('<span class="email">%s</span>' % unicode_to_html(email))


def unicode_to_html(text):
    """Turns all unicode into html entities, e.g. &#69; -> E."""
    return ''.join([u'&#%s;' % ord(i) for i in text])


@register.function
def user_list(users):
    """Turn a list of users into a list of links to their profiles."""
    link = u'<a href="%s">%s</a>'
    list = u', '.join([link % (escape(profile_url(u)), escape(u.username)) for
                       u in users])
    return Markup(list)


@register.function
def private_message(user):
    """Return a link to private message the user."""
    url = urlparams(reverse('messages.new'), to=user.username)
    msg = _('Private message')
    return Markup(u'<p class="pm"><a href="{url}">{msg}</a></p>'.format(
        url=url, msg=msg))
