from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User

from kitsune.sumo.urlresolvers import reverse


def _activate_users(admin, request, qs):
    num = qs.update(is_active=True)
    msg = '%s users activated.' % num if num != 1 else 'One user activated.'
    admin.message_user(request, msg)
_activate_users.short_description = u'Activate selected users'


def _deactivate_users(admin, request, qs):
    num = qs.update(is_active=False)
    msg = ('%s users deactivated.' % num if num != 1 else
           'One user deactivated.')
    admin.message_user(request, msg)
_deactivate_users.short_description = u'Deactivate selected users'


def patch_user_admin():
    """Prevent User objects from being deleted, even by superusers."""
    if not getattr(UserAdmin, '_monkeyed', False):
        UserAdmin._monkeyed = True
        UserAdmin.actions = [_activate_users, _deactivate_users]


def patch_user_model():
    """Add a more accurate User.get_absolute_url."""
    def get_absolute_url(self):
        return reverse('users.profile', args=[self.pk])
    User.get_absolute_url = get_absolute_url


def patch_all():
    patch_user_admin()
    patch_user_model()
