from functools import partial

from django.conf import settings
from django.contrib.auth.models import Group
from django.http import Http404, HttpResponseRedirect, HttpResponse
from django.views.decorators.http import require_GET

import jingo
from tower import ugettext as _

from access.decorators import login_required
from announcements.models import Announcement
from dashboards.personal import GROUP_DASHBOARDS
from dashboards.readouts import (overview_rows, READOUTS, L10N_READOUTS,
                                 CONTRIBUTOR_READOUTS)
from dashboards.utils import model_actions, render_readouts
from forums.models import Post
from sumo.urlresolvers import reverse
from sumo.utils import smart_int


def _kb_readout(request, readout_slug, readouts, locale=None, mode=None):
    """Instantiate and return the readout with the given slug.

    Raise Http404 if there is no such readout.

    """
    if readout_slug not in readouts:
        raise Http404
    return readouts[readout_slug](request, locale=locale, mode=mode)


def _kb_detail(request, readout_slug, readouts, main_view_name,
               main_dash_title, locale=None):
    """Show all the rows for the given KB article statistics table."""
    return jingo.render(request, 'dashboards/kb_detail.html',
        {'readout': _kb_readout(request, readout_slug, readouts, locale),
         'locale': locale,
         'main_dash_view': main_view_name,
         'main_dash_title': main_dash_title})


@require_GET
def contributors_detail(request, readout_slug):
    """Show all the rows for the given contributor dashboard table."""
    return _kb_detail(request, readout_slug, CONTRIBUTOR_READOUTS,
                      'dashboards.contributors', _('Contributor Dashboard'),
                      locale=settings.WIKI_DEFAULT_LANGUAGE)


@require_GET
def localization_detail(request, readout_slug):
    """Show all the rows for the given localizer dashboard table."""
    return _kb_detail(request, readout_slug, L10N_READOUTS,
                      'dashboards.localization', _('Localization Dashboard'))


@require_GET
def localization(request):
    """Render aggregate data about articles in a non-default locale."""
    if request.locale == settings.WIKI_DEFAULT_LANGUAGE:
        return HttpResponseRedirect(reverse('dashboards.contributors'))
    data = {'overview_rows': partial(overview_rows, request.locale)}
    return render_readouts(request, L10N_READOUTS, 'localization.html',
                           extra_data=data)


@require_GET
def contributors(request):
    """Render aggregate data about the articles in the default locale."""
    return render_readouts(request, CONTRIBUTOR_READOUTS, 'contributors.html',
                           locale=settings.WIKI_DEFAULT_LANGUAGE)


@require_GET
def wiki_rows(request, readout_slug):
    """Return the table contents HTML for the given readout and mode."""
    readout = _kb_readout(request, readout_slug, READOUTS,
                          locale=request.GET.get('locale'),
                          mode=smart_int(request.GET.get('mode'), None))
    max_rows = smart_int(request.GET.get('max'), fallback=None)
    return HttpResponse(readout.render(max_rows=max_rows))


@require_GET
@login_required
def review(request):
    """Review dashboard for a user, includes activity, announcements, etc."""
    return jingo.render(request, 'dashboards/review.html',
                        {'actions': model_actions(Post, request),
                         'announcements': Announcement.get_site_wide()})


@require_GET
@login_required
def group_dashboard(request, group_id):
    try:
        group = request.user.groups.get(pk=group_id)
    except Group.DoesNotExist:
        raise Http404

    return GROUP_DASHBOARDS[group.dashboard.dashboard](
        request, group.id, group.dashboard.parameters).render()
