from django.conf import settings
from django.contrib.auth.models import User

from jinja2 import escape, Markup
from jingo import register
from tower import ugettext as _

from kitsune.sumo.helpers import urlparams
from kitsune.sumo.urlresolvers import reverse
from kitsune.users.models import Profile


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
        return settings.STATIC_URL + settings.DEFAULT_AVATAR
    return (profile.avatar.url if profile and profile.avatar else
            settings.STATIC_URL + settings.DEFAULT_AVATAR)


@register.function
def display_name(user):
    """Return a display name if set, else the username."""
    try:  # Also mostly for tests.
        profile = user.get_profile()
    except Profile.DoesNotExist:
        return user.username
    return profile.name if profile and profile.name else user.username


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
    link = u'<a class="user" href="%s">%s</a>'
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


def suggest_username(email):
    username = email.split('@', 1)[0]

    username_regex = r'^{0}[0-9]*$'.format(username)
    users = User.objects.filter(username__regex=username_regex)

    if users.count() > 0:
        max_id = 0
        for u in users:
            # get the number at the end
            i = u.username[len(username):]

            # incase there's no number in the case where just the base is taken
            if i:
                i = int(i)
                if i > max_id:
                    max_id = i

        max_id += 1
        username = '{0}{1}'.format(username, max_id)

    return username
