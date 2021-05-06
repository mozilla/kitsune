import json

from django.forms import MultipleChoiceField, Widget
from django.forms.utils import flatatt
from django.utils.datastructures import MultiValueDict
from django.utils.encoding import force_text
from django.utils.html import escape
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _
from taggit.models import Tag


# TODO: Factor out dependency on taggit so it can be a generic large-vocab
# selector.
class TagWidget(Widget):
    """Widget which sticks each tag in a separate <input type=hidden>

    Designed to have the tag selection submitted all at once when a Submit
    button is clicked

    """

    # If True, render without editing controls:
    read_only = False

    # async_urls is a tuple: (URL for async add POSTs, URL for async remove
    # POSTs). If this is (), assume you want to queue up tag adds and removes
    # and submit them all at once through a form you wrap around this widget
    # yourself. In this case, tag names will not be links, because we'd have
    # to design some way of computing the URLs without hitting the network.
    async_urls = ()

    # make_link should be a function that takes a tag slug and returns some
    # kind of meaningful link. Ignored if async_urls is ().
    def make_link(self, slug):
        return "#"

    # Allow adding new tags to the vocab:
    can_create_tags = False

    # TODO: Add async_remove_url and async_add_url kwargs holding URLs to
    # direct async remove and add requests to. The client app is then
    # responsible for routing to those and doing the calls to remove/add
    # the tag.

    def _render_tag_list_items(self, control_name, tag_names):
        """Represent applied tags and render controls to allow removal."""

        def render_one(tag):
            output = '<li class="tag">'

            # Hidden input for form state:
            if not self.async_urls:
                output += "<input%s />" % flatatt(
                    {"value": force_text(tag.name), "type": "hidden", "name": control_name}
                )

                # Linkless tag name:
                output += '<span class="tag-name">%s</span>' % escape(tag.name)
            else:
                # Anchor for link to by-tag view:
                output += '<a class="tag-name" href="%s">%s</a>' % (
                    escape(self.make_link(tag.slug)),
                    escape(tag.name),
                )

            # Remove button:
            if not self.read_only:
                output += (
                    '<input type="submit" '
                    'value="&#x2716;" '
                    'class="remover" '
                    'name="remove-tag-%s" />' % escape(tag.name)
                )

            output += "</li>"
            return output

        tags = Tag.objects.filter(name__in=tag_names)
        representations = [render_one(t) for t in tags]
        return "\n".join(representations)

    def render(self, name, value, attrs=None, renderer=None):
        """Render a hidden input for each choice plus a blank text input."""
        output = '<div class="tag-adder tags%s"' % (
            "" if self.read_only or self.async_urls else " deferred"
        )
        if not self.read_only:
            vocab = [t.name for t in Tag.objects.only("name").all()]
            output += ' data-tag-vocab-json="%s"' % escape(json.dumps(vocab))
        if self.can_create_tags:
            output += ' data-can-create-tags="1"'
        output += ">"

        if not self.read_only:
            # Insert a hidden <input type=submit> before the removers so
            # hitting return doesn't wreak destruction:
            output += '<input type="submit" class="hidden-submitter" />'

        # TODO: Render the little form around the tags as a JS-less fallback
        # iff self.async_urls. And don't add the hidden Add button above.

        output += '<ul class="tag-list'
        if self.read_only:
            output += " immutable"
        output += '">'

        output += self._render_tag_list_items(name, value or [])

        output += "</ul>"

        # TODO: Add a TagField kwarg for synchronous tag add URL, and draw the
        # form here if it's filled out.

        if not self.read_only:
            # Add a field for inputting new tags. Since it's named the same as
            # the hidden inputs, it should handily work as a JS-less fallback.
            input_attrs = self.build_attrs(
                attrs, type="text", name=name, **{"class": "autocomplete-tags"}
            )
            output += "<input%s />" % flatatt(input_attrs)

            # Add the Add button:
            output += "<input%s />" % flatatt(
                dict(type="submit", value=_("Add"), **{"class": "adder"})
            )

        output += "</div>"
        return mark_safe(output)

    def value_from_datadict(self, data, files, name):
        # TODO: removed 'MergeDict' from classinfo check below
        # could find not explicit use of MergeDict elsewhere in the codebase, so
        # i think we're okay here?
        if isinstance(data, MultiValueDict):
            return data.getlist(name)
        return data.get(name, None)


class TagField(MultipleChoiceField):
    """A field semantically equivalent to a MultipleChoiceField--just with a
    list of choices so long that it would be awkward to display.

    The `choices` kwarg passed to the constructor should be a callable.

    If you use this, you'll probably also want to set many of the TagWidget's
    attrs after form instantiation. There's no opportunity to set them at
    construction, since TagField is typically instantiated deep within taggit.

    """

    widget = TagWidget

    # Unlike in the superclass, `choices` kwarg to __init__ is unused.

    def valid_value(self, value):
        """Check the validity of a single tag."""
        return self.widget.can_create_tags or Tag.objects.filter(name=value).exists()

    def to_python(self, value):
        """Ignore the input field if it's blank; don't make a tag called ''."""
        return [v for v in super(TagField, self).to_python(value) if v]
