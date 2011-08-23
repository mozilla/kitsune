"""
This monkeypatches Django to support the __html__ protocol used in Jinja
templates. Form, BoundField, ErrorList, and other form objects that
render HTML through their __unicode__ method are extended with __html__
so they can be rendered in Jinja templates without adding |safe.

Call the monkeypatch() function to execute the patch. It must be called
before django.forms is imported for the conditional_escape patch to work
properly. manage.py is the recommended location for calling monkeypatch().

Usage::

    import safe_django_forms
    safe_django_forms.monkeypatch()

The monkeypatch was developed as a real patch at
https://github.com/jbalogh/django/commits/safe.

"""
import django.utils.encoding
import django.utils.html
import django.utils.safestring


# This function gets directly imported within Django, so this change needs to
# happen before too many Django imports happen.
def conditional_escape(html):
    """
    Similar to escape(), except that it doesn't operate on pre-escaped strings.
    """
    if hasattr(html, '__html__'):
        return html.__html__()
    else:
        return django.utils.html.escape(html)


# Django uses SafeData to mark a string that has already been escaped or
# otherwise deemed safe. This __html__ method lets Jinja know about that too.
def __html__(self):
    """
    Returns the html representation of a string.

    Allows interoperability with other template engines.
    """
    return self


# Django uses StrAndUnicode for classes like Form, BoundField, Widget which
# have a __unicode__ method which returns escaped html. We replace
# StrAndUnicode with SafeStrAndUnicode to get the __html__ method.
class SafeStrAndUnicode(django.utils.encoding.StrAndUnicode):
    """A class whose __str__ and __html__ returns __unicode__."""

    def __html__(self):
        return unicode(self)


def monkeypatch():
    django.utils.html.conditional_escape = conditional_escape
    django.utils.safestring.SafeData.__html__ = __html__

    # forms imports have to come after we patch conditional_escape.
    from django.forms import forms, formsets, util, widgets

    # Replace StrAndUnicode with SafeStrAndUnicode in the inheritance
    # for all these classes.
    classes = (
        forms.BaseForm,
        forms.BoundField,
        formsets.BaseFormSet,
        util.ErrorDict,
        util.ErrorList,
        widgets.Media,
        widgets.RadioInput,
        widgets.RadioFieldRenderer,
    )

    for cls in classes:
        bases = list(cls.__bases__)
        if django.utils.encoding.StrAndUnicode in bases:
            idx = bases.index(django.utils.encoding.StrAndUnicode)
            bases[idx] = SafeStrAndUnicode
            cls.__bases__ = tuple(bases)
