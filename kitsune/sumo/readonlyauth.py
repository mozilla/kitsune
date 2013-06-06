class ReadOnlyBackend(object):
    """Django auth backend for readonly mode

    The whole purpose of this is to reject everything.  It should
    implement all the methods that
    django.contrib.auth.backends.ModelBackend has.

    """

    def authenticate(self, *args, **kwargs):
        return None

    def get_group_permissions(self, *args, **kwargs):
        return set()

    def get_all_permissions(self, *args, **kwargs):
        return set()

    def has_perm(self, *args, **kwargs):
        return False

    def has_module_perms(self, *args, **kwargs):
        return False

    def get_user(self, *args, **kwargs):
        return None
