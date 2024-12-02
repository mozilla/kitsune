import json

from django_jinja import library

from kitsune.tags.models import SumoTag


@library.global_function
def tags_to_text(tags):
    """Converts a list of tag objects into a comma-separated slug list."""
    return ",".join([t.slug for t in tags])


@library.global_function
def tag_vocab():
    """Returns the tag vocabulary as a JSON object."""
    return json.dumps(
        dict((t[0], t[1]) for t in SumoTag.objects.active().values_list("name", "slug"))
    )
