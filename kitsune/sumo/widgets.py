# Based on http://djangosnippets.org/snippets/1580/
from django import forms


class ImageWidget(forms.FileInput):
    """
    A ImageField Widget that shows a thumbnail.
    """

    def __init__(self, attrs=None):
        if attrs is None:
            attrs = {}
        super().__init__(attrs)

    def render(self, name, value, attrs=None, renderer=None):
        output = super().render(name, value, attrs, renderer=renderer)
        if value and hasattr(value, "url"):
            output = '<div class="val-wrap"><img src="{}" alt="" />{}</div>'.format(value.url, output)
        return output
