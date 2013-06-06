from django.db.models import Q

from jingo import register

from kitsune.karma.models import Title


@register.function
def karma_titles(user):
    """Return a list of titles for a given user."""
    # Titles assigned to the user or groups
    return Title.objects.filter(
        Q(users=user) | Q(groups__in=user.groups.all())).distinct()
