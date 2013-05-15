import colorsys
import json
import logging
import math

from django.conf import settings
from django.contrib.auth.models import Group
from django.http import Http404, HttpResponseRedirect, HttpResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_GET

from tower import ugettext as _

from access.decorators import login_required
from announcements.views import user_can_announce
from dashboards.personal import GROUP_DASHBOARDS, personal_dashboards
from dashboards.readouts import (overview_rows, READOUTS, L10N_READOUTS,
                                 CONTRIBUTOR_READOUTS)
from dashboards.utils import render_readouts
from products.models import Product
from sumo.urlresolvers import reverse
from sumo.utils import smart_int
from users.helpers import profile_url
from wiki.models import Locale


log = logging.getLogger('k.dashboards')


def _kb_readout(request, readout_slug, readouts, locale=None, mode=None,
                product=None):
    """Instantiate and return the readout with the given slug.

    Raise Http404 if there is no such readout.

    """
    if readout_slug not in readouts:
        raise Http404
    return readouts[readout_slug](request, locale=locale, mode=mode,
                                  product=product)


def _kb_detail(request, readout_slug, readouts, main_view_name,
               main_dash_title, locale=None, product=None):
    """Show all the rows for the given KB article statistics table."""
    return render(request, 'dashboards/kb_detail.html', {
        'readout': _kb_readout(request, readout_slug, readouts, locale,
                               product=product),
        'locale': locale,
        'main_dash_view': main_view_name,
        'main_dash_title': main_dash_title,
        'product': product,
        'products': Product.objects.filter(visible=True)})


@require_GET
def contributors_detail(request, readout_slug):
    """Show all the rows for the given contributor dashboard table."""
    product = _get_product(request)

    return _kb_detail(request, readout_slug, CONTRIBUTOR_READOUTS,
                      'dashboards.contributors', _('Knowledge Base Dashboard'),
                      locale=settings.WIKI_DEFAULT_LANGUAGE, product=product)


@require_GET
def localization_detail(request, readout_slug):
    """Show all the rows for the given localizer dashboard table."""
    product = _get_product(request)

    return _kb_detail(request, readout_slug, L10N_READOUTS,
                      'dashboards.localization', _('Localization Dashboard'),
                      product=product)


@require_GET
def localization(request):
    """Render aggregate data about articles in a non-default locale."""
    if request.LANGUAGE_CODE == settings.WIKI_DEFAULT_LANGUAGE:
        return HttpResponseRedirect(reverse('dashboards.contributors'))
    locales = Locale.objects.filter(locale=request.LANGUAGE_CODE)
    if locales:
        permission = user_can_announce(request.user, locales[0])
    else:
        permission = False

    product = _get_product(request)

    data = {
      'overview_rows': overview_rows(request.LANGUAGE_CODE, product=product),
      'user_can_announce': permission
    }
    return render_readouts(request, L10N_READOUTS, 'localization.html',
                           extra_data=data, product=product)


@require_GET
def contributors(request):
    """Render aggregate data about the articles in the default locale."""
    product = _get_product(request)

    return render_readouts(
        request,
        CONTRIBUTOR_READOUTS,
        'contributors.html',
        locale=settings.WIKI_DEFAULT_LANGUAGE,
        product=product)


@require_GET
def wiki_rows(request, readout_slug):
    """Return the table contents HTML for the given readout and mode."""
    product = _get_product(request)

    readout = _kb_readout(request, readout_slug, READOUTS,
                          locale=request.GET.get('locale'),
                          mode=smart_int(request.GET.get('mode'), None),
                          product=product)
    max_rows = smart_int(request.GET.get('max'), fallback=None)
    return HttpResponse(readout.render(max_rows=max_rows))


@require_GET
@login_required
def group_dashboard(request, group_id):
    try:
        group = request.user.groups.get(pk=group_id)
    except Group.DoesNotExist:
        raise Http404

    return GROUP_DASHBOARDS[group.dashboard.dashboard](
        request, group.id, group.dashboard.parameters).render()


@require_GET
@login_required
def default_dashboard(request):
    dashboards = personal_dashboards(request)
    if len(dashboards) > 0:
      # Redirect to the first dashboard
      return HttpResponseRedirect(dashboards[0].get_absolute_url())
    else:
      # Redirect to the profile page
      return HttpResponseRedirect(profile_url(request.user))


def _get_product(request):
    product_slug = request.GET.get('product')
    if product_slug:
        return get_object_or_404(Product, slug=product_slug)

    return None
