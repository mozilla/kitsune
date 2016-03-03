from django.db.models import Q

from django_jinja import library

from kitsune.karma.models import Title


@library.global_function
def karma_titles(user):
    """Return a list of titles for a given user."""
    # Titles assigned to the user or groups
    return Title.objects.filter(
        Q(users=user) | Q(groups__in=user.groups.all())).distinct()
