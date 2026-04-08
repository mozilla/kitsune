import json

from django_jinja import library

from kitsune.tags.models import SumoTag


@library.global_function
def tags_to_text(tags):
    """Converts a list of tag objects into a comma-separated slug list."""
    return ",".join([t.slug for t in tags])


@library.global_function
def toggle_tag_slug(tagged_csv, slug):
    """Toggle a tag slug in a comma-separated slug string.

    Returns the updated string, or None if the result is empty.
    """
    slugs = [s for s in tagged_csv.split(",") if s] if tagged_csv else []
    if slug in slugs:
        slugs = [s for s in slugs if s != slug]
    else:
        slugs.append(slug)
    return ",".join(slugs) or None


@library.global_function
def tag_vocab():
    """Returns the tag vocabulary as a JSON object."""
    return json.dumps({t[0]: t[1] for t in SumoTag.objects.active().values_list("name", "slug")})
