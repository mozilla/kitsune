from badger.models import Badge


def get_or_create_badge(slug, **kwargs):
    """Get or create a badge.

    If a badge with the specified slug doesn't exist, we create
    the badge with the specified slug and kwargs.
    """
    try:
        return Badge.objects.get(slug=slug)
    except Badge.DoesNotExist:
        return Badge.objects.create(slug=slug, **kwargs)
