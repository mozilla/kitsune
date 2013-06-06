from functools import partial

from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import render
from django.utils.datastructures import SortedDict

from kitsune.announcements.models import Announcement
from kitsune.dashboards.readouts import (
    overview_rows, GROUP_CONTRIBUTOR_READOUTS, GROUP_L10N_READOUTS)
from kitsune.dashboards.utils import model_actions, render_readouts
from kitsune.questions.models import Answer


class Dashboard(object):
    """Abstract base class for user or group ("personal") dashboards

    Renders using self.render()

    """
    # Slug is stored in the DB and required to associate with classes.
    # slug = 'some-dash'
    # render() = render your dashboard, returns straight to a view.

    def __init__(self, request, id, params):
        """
        Args:
            request: an HTTP request
            id: a GroupDashboard's id
            params: a GroupDashboard's parameters

        """
        self._request = request
        self._params = params
        self._id = id

    def render(self):
        """Override this to render your dashboard."""
        return HttpResponse('Hi, I am a group dashboard.')


class QuestionsDashboard(Dashboard):
    slug = 'forum'

    def render(self):
        return render(
            self._request,
            'dashboards/questions.html',
            {'actions': model_actions(Answer, self._request),
             'active_tab': self._id,
             'announcements': Announcement.get_for_group_id(self._id)})


class LocaleDashboard(Dashboard):
    slug = 'locale'

    def render(self):
        """Locale dashboard for a group."""
        locale = self._params.strip()
        data = {}
        if locale == settings.WIKI_DEFAULT_LANGUAGE:
            readouts = GROUP_CONTRIBUTOR_READOUTS
        else:
            readouts = GROUP_L10N_READOUTS
            data['overview_rows'] = partial(overview_rows, locale)
        data['announcements'] = Announcement.get_for_group_id(self._id)
        data['active_tab'] = self._id
        return render_readouts(self._request, readouts, 'group_locale.html',
                               extra_data=data, locale=locale)


def personal_dashboards(request):
    """Return an iterable of parametrized dashboards to show, given a request.

    We might decide based on the user, the locale, etc.

    """
    from kitsune.dashboards.models import GroupDashboard

    # Gather dashboards the user has access to:
    # Must fall back to [] because __in=<Empty QuerySet> fails.
    user_groups = request.user.groups.all() or []
    return GroupDashboard.objects.filter(
        group__in=user_groups).order_by('group__name')


# Shown only when mapped to a group:
GROUP_DASHBOARDS = SortedDict((d.slug, d) for d in
    [QuestionsDashboard, LocaleDashboard])
