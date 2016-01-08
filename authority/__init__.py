import sys

from authority.sites import site, get_check, get_choices_for, register, unregister  # noqa

LOADING = False


def autodiscover():
    """
    Goes and imports the permissions submodule of every app in INSTALLED_APPS
    to make sure the permission set classes are registered correctly.
    """
    global LOADING
    if LOADING:
        return
    LOADING = True

    import imp
    from django.conf import settings

    for app in settings.INSTALLED_APPS:
        try:
            __import__(app)
            app_path = sys.modules[app].__path__
        except AttributeError:
            continue
        try:
            imp.find_module('permissions', app_path)
        except ImportError:
            continue
        __import__("%s.permissions" % app)
        app_path = sys.modules["%s.permissions" % app]
    LOADING = False
