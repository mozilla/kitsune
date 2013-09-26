from badger.models import Badge


def get_or_create_badge(badge_template, year=None):
    """Get or create a badge.

    The badge_template is a dict and must have a slug key. All
    the values in the dict will be formatted with year, if one
    is specified. For example:
        badge_template['slug'].format(year=year)

    If a badge with the specified slug doesn't exist, we create
    the badge with the specified slug and the rest of the items
    in the dict.
    """
    if year is not None:
        badge_template = dict(
            (key, value.format(year=year)) for (key, value) in
            badge_template.items())

    slug = badge_template.pop('slug')

    try:
        return Badge.objects.get(slug=slug)
    except Badge.DoesNotExist:
        return Badge.objects.create(slug=slug, **badge_template)
