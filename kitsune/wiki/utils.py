from django.contrib.auth.models import User
from django.db.models import Q

from kitsune.wiki.models import Revision


def active_contributors(from_date, to_date=None, locale=None, product=None):
    """Return active KB contributors for the specified parameters.

    An active KB contributor is a user that has created or reviewed a
    Revision in the given time period.

    :arg from_date: start date for contributions to be included
    :arg to_date: end date for contributions to be included
    :arg locale: (optional) locale to filter on
    :arg product: (optional) only count documents for a product
    """
    return User.objects.filter(
        id__in=_active_contributors_id(from_date, to_date, locale, product))


def num_active_contributors(from_date, to_date=None, locale=None,
                            product=None):
    """Return number of active KB contributors for the specified parameters.

    An active KB contributor is a user that has created or reviewed a
    Revision in the given time period.

    :arg from_date: start date for contributions to be included
    :arg to_date: end date for contributions to be included
    :arg locale: (optional) locale to filter on
    :arg product: (optional) only count documents for a product
    """
    return len(_active_contributors_id(from_date, to_date, locale, product))


def _active_contributors_id(from_date, to_date, locale, product):
    """Return the set of ids for the top contributors based on the params.

    An active KB contributor is a user that has created or reviewed a
    Revision in the given time period.

    :arg from_date: start date for contributions to be included
    :arg to_date: end date for contributions to be included
    :arg locale: (optional) locale to filter on
    :arg product: (optional) only count documents for a product
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

    if product:
        editors = editors.filter(
            Q(document__products=product) |
            Q(document__parent__products=product))
        reviewers = reviewers.filter(
            Q(document__products=product) |
            Q(document__parent__products=product))

    return set(list(editors) + list(reviewers))
