import random
from string import letters

from django.contrib.auth.models import User, Group, Permission
from django.contrib.contenttypes.models import ContentType

from kitsune.sumo.tests import LocalizingClient, TestCase, with_save
from kitsune.users.models import Profile, Setting


class TestCaseBase(TestCase):
    """Base TestCase for the users app test cases."""

    client_class = LocalizingClient


def profile(**kwargs):
    """Return a saved profile for a given user."""
    # Many tests check for user identity based on the display name, so it's
    # helpful to make `name` here probably unique.
    defaults = {
        'name': 'Test K. User ({0})'.format(random.randint(0, 1000)),
        'bio': 'Some bio.',
        'website': 'http://support.mozilla.com',
        'timezone': None,
        'country': 'US',
        'city': 'Mountain View',
        'locale': 'en-US',
    }
    if 'user' not in kwargs:
        u = user(save=True)
        defaults['user'] = u
    defaults.update(kwargs)

    p = Profile(**defaults)
    p.save()
    return p


@with_save
def user(**kwargs):
    """Return a user with all necessary defaults filled in.

    Default password is 'testpass' unless you say otherwise in a kwarg.

    """
    defaults = {}
    if 'username' not in kwargs:
        defaults['username'] = ''.join(random.choice(letters)
                                       for x in xrange(15))
    if 'email' not in kwargs:
        defaults['email'] = ''.join(
            random.choice(letters) for x in xrange(10)) + '@example.com'
    defaults.update(kwargs)
    user = User(**defaults)
    user.set_password(kwargs.get('password', 'testpass'))
    return user


@with_save
def group(**kwargs):
    defaults = {}
    if 'name' not in kwargs:
        defaults['name'] = ''.join(random.choice(letters) for x in xrange(15))
    defaults.update(kwargs)
    return Group(**defaults)


def add_permission(user, model, permission_codename):
    """Add a permission to a user.

    Creates the permission if it doesn't exist.

    """
    content_type = ContentType.objects.get_for_model(model)
    try:
        permission = Permission.objects.get(codename=permission_codename,
                                            content_type=content_type)
    except Permission.DoesNotExist:
        permission = Permission.objects.create(codename=permission_codename,
                                               name=permission_codename,
                                               content_type=content_type)
    user.user_permissions.add(permission)


@with_save
def setting(**kwargs):
    defaults = {
        'name': ''.join(random.choice(letters) for _ in range(10)),
        'value': ''.join(random.choice(letters) for _ in range(10)),
    }
    defaults.update(kwargs)
    return Setting(**defaults)
