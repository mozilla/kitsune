from django.db.models import Q

from jingo import register

from karma.models import Title


@register.function
def karma_titles(user):
    """Return a list of titles for a given user."""
    # Custom titles assigned to the user or groups
    titles = Title.objects.filter(Q(users=user) |
                                  Q(groups__in=user.groups.all())).distinct()
    # TODO: Append auto-titles (top contributors, etc)
    # TODO: Cache the result
    return titles
