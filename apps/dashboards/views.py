from functools import partial

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.http import Http404, HttpResponseRedirect, HttpResponse
from django.utils.datastructures import SortedDict
from django.views.decorators.http import require_GET

import jingo
from tower import ugettext as _

from access.decorators import login_required
from announcements.models import Announcement
from dashboards import ACTIONS_PER_PAGE
from dashboards.personal import (ReviewDashboard, QuestionsDashboard,
                                 LocaleDashboard)
from dashboards.readouts import (overview_rows, READOUTS, L10N_READOUTS,
                                 CONTRIBUTOR_READOUTS, GROUP_L10N_READOUTS,
                                 GROUP_CONTRIBUTOR_READOUTS)
from forums.models import Post
from sumo_locales import LOCALES
from sumo.urlresolvers import reverse
from sumo.utils import paginate, smart_int
from questions.models import Answer
from wiki.events import (ApproveRevisionInLocaleEvent,
                         ReviewableRevisionInLocaleEvent)


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


def _kb_main(request, readouts, template, locale=None, extra_data=None):
    """Render a KB statistics overview page.

    Use the given template, pass the template the given readouts, limit the
    considered data to the given locale, and pass along anything in the
    `extra_data` dict to the template in addition to the standard data.

    """
    current_locale = locale or request.locale
    data = {'readouts': SortedDict((slug, class_(request, locale=locale))
                         for slug, class_ in readouts.iteritems()),
            'default_locale': settings.WIKI_DEFAULT_LANGUAGE,
            'default_locale_name':
                LOCALES[settings.WIKI_DEFAULT_LANGUAGE].native,
            'current_locale': current_locale,
            'current_locale_name': LOCALES[current_locale].native,
            'is_watching_approved': ApproveRevisionInLocaleEvent.is_notifying(
                request.user, locale=request.locale),
            'is_watching_locale': ReviewableRevisionInLocaleEvent.is_notifying(
                request.user, locale=request.locale),
            'is_watching_approved_default':
                ApproveRevisionInLocaleEvent.is_notifying(
                    request.user, locale=settings.WIKI_DEFAULT_LANGUAGE)}
    if extra_data:
        data.update(extra_data)
    return jingo.render(request, 'dashboards/' + template, data)


@require_GET
def localization(request):
    """Render aggregate data about articles in a non-default locale."""
    if request.locale == settings.WIKI_DEFAULT_LANGUAGE:
        return HttpResponseRedirect(reverse('dashboards.contributors'))
    data = {'overview_rows': partial(overview_rows, request.locale)}
    return _kb_main(request, L10N_READOUTS, 'localization.html',
                    extra_data=data)


@require_GET
def contributors(request):
    """Render aggregate data about the articles in the default locale."""
    return _kb_main(request, CONTRIBUTOR_READOUTS, 'contributors.html',
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
                        {'actions': _actions(Post, request),
                         'announcements': Announcement.get_site_wide(),
                         'dashboard_signature':
                             ReviewDashboard(request).signature})


@require_GET
@login_required
def questions(request):
    """Support Forum dashboard for a user"""
    return jingo.render(request, 'dashboards/questions.html',
                        {'actions': _actions(Answer, request),
                         'announcements': Announcement.get_site_wide(),
                         'dashboard_signature':
                             QuestionsDashboard(request).signature})


@require_GET
def group_locale(request, explicit_locale):
    """Group Locale dashboard for a locale group."""
    data = {}
    if explicit_locale == settings.WIKI_DEFAULT_LANGUAGE:
        readouts = GROUP_CONTRIBUTOR_READOUTS
    else:
        readouts = GROUP_L10N_READOUTS
        data['overview_rows'] = partial(overview_rows, explicit_locale)
    data['announcements'] = Announcement.get_for_groups(
        request.user.groups.all())
    data['dashboard_signature'] = LocaleDashboard(
        request, explicit_locale).signature
    return _kb_main(request, readouts, 'group_locale.html',
                    extra_data=data, locale=explicit_locale)


def _actions(model_class, request):
    """Returns paginated activity for the given model."""
    ct = ContentType.objects.get_for_model(model_class)
    actions = request.user.action_inbox.filter(content_type=ct)
    return paginate(request, actions, per_page=ACTIONS_PER_PAGE)
