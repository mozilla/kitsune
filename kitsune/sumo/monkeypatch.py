import sys
from functools import wraps

from django.forms import fields


_has_been_patched = False
TESTING = (len(sys.argv) > 1 and sys.argv[1] == "test") or sys.argv[0].endswith("py.test")


class DateWidget(fields.DateField.widget):
    input_type = "date"

    def __init__(self, *args, **kwargs):
        # force format to be what <input type="date"> expects, regardless of locale
        kwargs["format"] = "%Y-%m-%d"
        super().__init__(*args, **kwargs)


class TimeWidget(fields.TimeField.widget):
    input_type = "time"

    def __init__(self, *args, **kwargs):
        # force format to be what <input type="time"> expects, regardless of locale
        kwargs["format"] = "%H:%M"
        super().__init__(*args, **kwargs)


def patch():
    global _has_been_patched

    if _has_been_patched:
        return

    fields.DateField.widget = DateWidget
    fields.TimeField.widget = TimeWidget

    # Workaround until https://code.djangoproject.com/ticket/16920 gets fixed.
    from django.contrib.admin import utils
    from django.contrib.admin.utils import NestedObjects
    from django.db import models

    def _collect(self, objs, source_attr=None, **kwargs):
        for obj in objs:
            if source_attr:
                # We just added a default of None below and that gets around
                # the problem.
                self.add_edge(getattr(obj, source_attr, None), obj)
            else:
                self.add_edge(None, obj)
        try:
            return super(NestedObjects, self).collect(objs, source_attr=source_attr, **kwargs)
        except models.ProtectedError as e:
            self.protected.update(e.protected_objects)

    utils.NestedObjects.collect = _collect

    # Monkey-patch admin site.
    from django.contrib import admin
    from adminplus.sites import AdminSitePlus

    # Patch the admin
    admin.site = AdminSitePlus()
    admin.sites.site = admin.site
    admin.site.site_header = "Kitsune Administration"
    admin.site.site_title = "Mozilla Support"

    # In testing contexts, patch django.shortcuts.render
    if TESTING:
        monkeypatch_render()

    _has_been_patched = True


def monkeypatch_render():
    """
    Monkeypatches django.shortcuts.render for Jinja2 kung-fu action

    .. Note::
       Only call this in a testing context!
    """
    import django.shortcuts

    def more_info(fun):
        """Django's render shortcut, but captures information for testing
        When using Django's render shortcut with Jinja2 templates, none of
        the information is captured and thus you can't use it for testing.
        This alleviates that somewhat by capturing some of the information
        allowing you to test it.
        Caveats:
        * it does *not* capture all the Jinja2 templates used to render.
        Only the topmost one requested by the render() function.
        """

        @wraps(fun)
        def _more_info(request, template_name, *args, **kwargs):
            resp = fun(request, template_name, *args, **kwargs)

            resp.jinja_templates = [template_name]
            if args:
                resp.jinja_context = args[0]
            elif "context" in kwargs:
                resp.jinja_context = kwargs["context"]
            else:
                resp.jinja_context = {}

            return resp

        return _more_info

    django.shortcuts.render = more_info(django.shortcuts.render)
