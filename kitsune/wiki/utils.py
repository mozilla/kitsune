from django.contrib.auth.models import User

from kitsune.wiki.models import Revision


def active_contributors(from_date, to_date=None, locale=None):
    """Return active KB contributors for the specified dates and locale.

    An active KB contributor is a user that has created or reviewed a
    Revision in the given time period.

    :arg from_date: start date for contributions to be included
    :arg to_date: end date for contributions to be included
    :arg locale: (optional) locale to filter on
    """
    editors = (Revision.objects
        .filter(created__gte=from_date)
        .values_list('creator', flat=True).distinct())

    reviewers = (Revision.objects
        .filter(reviewed__gte=from_date)
        .values_list('reviewer', flat=True).distinct())

    if to_date:
        editors = editors.filter(created__lt=to_date)
        reviewers = reviewers.filter(reviewed__lt=to_date)

    if locale:
        editors = editors.filter(document__locale=locale)
        reviewers = reviewers.filter(document__locale=locale)

    return User.objects.filter(id__in=set(list(editors) + list(reviewers)))
