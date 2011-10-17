from django.forms import fields

# Monkey patch preserves the old values, so we can pick up any changes
# in CharField.widget_attrs and Field.widget_attrs
# paulc filed a Django ticket for it, #14884
field_widget_attrs = fields.Field.widget_attrs
charfield_widget_attrs = fields.CharField.widget_attrs


def required_field_attrs(self, widget):
    """This function is for use on the base Field class."""
    attrs = field_widget_attrs(self, widget)
    if self.required and not 'required' in attrs:
        attrs['required'] = 'required'
    return attrs


def required_char_field_attrs(self, widget, *args, **kwargs):
    """This function is for use on the CharField class."""
    # We need to call super() here, since Django's CharField.widget_attrs
    # doesn't call its super and thus won't use the required_field_attrs above.
    attrs = super(fields.CharField, self).widget_attrs(widget, *args, **kwargs)
    original_attrs = charfield_widget_attrs(self, widget) or {}
    attrs.update(original_attrs)
    return attrs


class DateWidget(fields.DateField.widget):
    input_type = 'date'


class TimeWidget(fields.TimeField.widget):
    input_type = 'time'


class URLWidget(fields.URLField.widget):
    input_type = 'url'


class EmailWidget(fields.EmailField.widget):
    input_type = 'email'


fields.Field.widget_attrs = required_field_attrs
fields.CharField.widget_attrs = required_char_field_attrs
fields.DateField.widget = DateWidget
fields.TimeField.widget = TimeWidget
fields.URLField.widget = URLWidget
fields.EmailField.widget = EmailWidget


# Workaround until https://code.djangoproject.com/ticket/16920 gets fixed.
from django.contrib.admin import util
from django.contrib.admin.util import NestedObjects

def _collect(self, objs, source_attr=None, **kwargs):
    for obj in objs:
        if source_attr:
            # We just added a default of None below and that gets around
            # the problem.
            self.add_edge(getattr(obj, source_attr, None), obj)
        else:
            self.add_edge(None, obj)
    try:
        return super(NestedObjects, self).collect(
            objs, source_attr=source_attr, **kwargs)
    except models.ProtectedError, e:
        self.protected.update(e.protected_objects)

util.NestedObjects.collect = _collect
