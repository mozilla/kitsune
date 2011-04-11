from django.utils.datastructures import SortedDict

from tower import ugettext_lazy as _lazy

from sumo.urlresolvers import reverse
from users.helpers import profile_url


class Dashboard(object):
    """Abstract base class for user or group ("personal") dashboards

    Compares and hashes according to the value of its fields so that
    identically parametrized dashboards of the same class end up
    de-duplicating.

    """
    # Value of the "active" template var when this dash is active. Wouldn't
    # hurt to be a valid CSS class name. Class attr.
    # slug = 'some-dash'

    # If a dashboard's URL is invariant, just define a reversible view path:
    # _view = 'some.view'

    # Instance attr:
    # title = _lazy(u'Title for tab')

    def __init__(self, request, params=''):
        """Override to unpack and retain parameters in the dict self._params.

        Don't stick params anywhere else, as only self._params will be
        considered when comparing or hashing.

        Args:
            params: string params from a GroupDashboard

        """
        self._params = {}
        self._request = request

    def __eq__(self, other):
        return (self.__class__ is other.__class__ and
                getattr(self, '_params', None) ==
                getattr(other, '_params', None))

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        items = self._params.items()
        items.sort()
        # Different subclasses should hash differently:
        items.append(self.__class__)
        return hash(tuple(items))

    @property
    def url(self):
        """Default implementation which reverses self._view"""
        return reverse(self._view)


class QuestionsDashboard(Dashboard):
    slug = 'forum'
    _view = 'dashboards.questions'
    title = _lazy(u'Forum')


class ReviewDashboard(Dashboard):
    slug = 'review'
    _view = 'dashboards.review'
    title = _lazy(u'Review', 'dashboard')


# TODO: enable
# class MyLocale(Dashboard):
#     slug = 'my-locale'
#     view = 'dashboards.localization'
#     title = _lazy(u'My locale')


class ProfileDashboard(Dashboard):
    slug = 'my-profile'
    title = _lazy(u'My profile')

    @property
    def url(self):
        return profile_url(self._request.user)


class EditProfileDashboard(Dashboard):
    slug = 'edit-profile'
    _view = 'users.edit_profile'
    title = _lazy(u'Edit my profile')


def personal_dashboards(request):
    """Return an iterable of parametrized dashboards to show, given a request.

    We might decide based on the user, the locale, etc.

    """
    from dashboards.models import GroupDashboard

    # Gather dashboards the user has access to:
    group_dashes = GroupDashboard.objects.filter(
        group__in=request.user.groups.all())

    # Parametrize dashboard classes, and uniquify on class and params:
    dashes = set()
    dashes.update(DYNAMIC_DASHBOARDS[g.dashboard](request, g.parameters)
                  for g in group_dashes
                  if g.dashboard in DYNAMIC_DASHBOARDS)

    # Sort the dynamic dashboards:
    sorted_dashes = list(dashes)
    # TODO: When we need a real sort order, do something about it:
    sorted_dashes.sort(key=lambda dash: dash.slug)

    # Prepend the always-shown static dashboards ones:
    return [d(request) for d in STATIC_DASHBOARDS] + sorted_dashes


# Dashboards always shown:
STATIC_DASHBOARDS = [
    ReviewDashboard, ProfileDashboard, EditProfileDashboard]

# Shown only when mapped to a group:
DYNAMIC_DASHBOARDS = SortedDict((d.slug, d) for d in [QuestionsDashboard])
