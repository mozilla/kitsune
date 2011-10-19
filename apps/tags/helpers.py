from jingo import register


@register.function
def tags_to_text(tags):
    """Converts a list of tag objects into a comma-separated slug list."""
    return ','.join([t.slug for t in tags])
