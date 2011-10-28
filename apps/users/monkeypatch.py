from django.contrib.auth.admin import UserAdmin


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
        UserAdmin.has_delete_permission = lambda *a, **kw: False
        UserAdmin.actions = [_activate_users, _deactivate_users]
