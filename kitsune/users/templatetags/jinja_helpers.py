import hashlib
import urllib

from django.conf import settings
from django.utils.encoding import force_str
from django.utils.translation import ugettext as _

from django_jinja import library
from jinja2 import escape, Markup

from kitsune.sumo.templatetags.jinja_helpers import urlparams
from kitsune.sumo.urlresolvers import reverse
from kitsune.users.models import Profile


@library.global_function
def get_profile(user):
    try:
        return Profile.objects.get(user_id=user.id)
    except Profile.DoesNotExist:
        return None


@library.global_function
def profile_url(user, edit=False):
    """Return a URL to the user's profile."""
    if edit:
        return reverse('users.edit_profile', args=[user.username])
    return reverse('users.profile', args=[user.username])


@library.global_function
def profile_avatar(user, size=48):
    """Return a URL to the user's avatar."""
    try:  # This is mostly for tests.
        profile = Profile.objects.get(user_id=user.id)
    except (Profile.DoesNotExist, AttributeError):
        avatar = settings.STATIC_URL + settings.DEFAULT_AVATAR
    else:
        if profile.is_fxa_migrated:
            avatar = profile.fxa_avatar
        elif profile.avatar:
            avatar = profile.avatar.url
        else:
            avatar = settings.STATIC_URL + settings.DEFAULT_AVATAR

    if avatar.startswith('//'):
        avatar = 'https:%s' % avatar

    if user and hasattr(user, 'email'):
        email_hash = hashlib.md5(force_str(user.email.lower())).hexdigest()
    else:
        email_hash = '00000000000000000000000000000000'

    url = 'https://secure.gravatar.com/avatar/%s?s=%s' % (email_hash, size)

    # If the url doesn't start with http (local dev), don't pass it to
    # to gravatar because it can't use it.
    if avatar.startswith('https') and profile and profile.is_fxa_migrated:
        url = avatar
    elif avatar.startswith('http'):
        url = url + '&d=%s' % urllib.quote(avatar)

    return url


@library.global_function
def display_name(user):
    """Return a display name if set, else the username."""
    try:  # Also mostly for tests.
        profile = Profile.objects.get(user_id=user.id)
    except (Profile.DoesNotExist, AttributeError):
        return user.username
    return profile.display_name if profile else user.username


@library.filter
def public_email(email):
    """Email address -> publicly displayable email."""
    return Markup('<span class="email">%s</span>' % unicode_to_html(email))


def unicode_to_html(text):
    """Turns all unicode into html entities, e.g. &#69; -> E."""
    return ''.join([u'&#%s;' % ord(i) for i in text])


@library.global_function
def user_list(users):
    """Turn a list of users into a list of links to their profiles."""
    link = u'<a class="user" href="%s">%s</a>'
    list = u', '.join([link % (escape(profile_url(u)), escape(display_name(u))) for
                       u in users])
    return Markup(list)


@library.global_function
def private_message(user):
    """Return a link to private message the user."""
    url = urlparams(reverse('messages.new'), to=user.username)
    msg = _('Private message')
    return Markup(u'<p class="pm"><a href="{url}">{msg}</a></p>'.format(
        url=url, msg=msg))


@library.global_function
def is_contributor(user):
    """Return whether the user is in the 'Registered as contributor' group."""
    return (user.is_authenticated() and
            user.groups.filter(name='Registered as contributor').count() > 0)
