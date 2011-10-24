import json

from jingo import register
from taggit.models import Tag


@register.function
def tags_to_text(tags):
    """Converts a list of tag objects into a comma-separated slug list."""
    return ','.join([t.slug for t in tags])


@register.function
def tag_vocab():
    """Returns the tag vocabulary as JSON array."""
    return json.dumps(list(Tag.objects.values_list('name', flat=True)))
