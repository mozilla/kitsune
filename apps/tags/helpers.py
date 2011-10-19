from jingo import register


@register.function
def remove_tag(tags, tag):
    """Removes a tag from a list of tags."""
    return [t for t in tags if t != tag]


@register.function
def tags_to_text(tags):
    """Converts a list of tag objects into a comma-separated slug list."""
    return ','.join([t.slug for t in tags])
