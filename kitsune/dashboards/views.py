import json
import logging
from datetime import date, timedelta

from django.conf import settings
from django.http import Http404, HttpResponseRedirect, HttpResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_GET

from tower import ugettext as _

from kitsune.announcements.views import user_can_announce
from kitsune.dashboards.readouts import (
    overview_rows, READOUTS, L10N_READOUTS, CONTRIBUTOR_READOUTS)
from kitsune.dashboards.utils import render_readouts, get_locales_by_visit
from kitsune.products.models import Product
from kitsune.sumo.urlresolvers import reverse
from kitsune.sumo.utils import smart_int
from kitsune.wiki.models import Locale


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
        'overview_rows': overview_rows(
            request.LANGUAGE_CODE, product=product),
        'user_can_announce': permission,
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
def locale_metrics(request, locale_code):
    """The kb metrics dashboard for a specific locale."""

    if locale_code not in settings.SUMO_LANGUAGES:
        raise Http404

    product = _get_product(request)

    return render(
        request,
        'dashboards/locale_metrics.html',
        {
            'current_locale': locale_code,
            'product': product,
            'products': Product.objects.filter(visible=True),
        })


@require_GET
def aggregated_metrics(request):
    """The aggregated (all locales) kb metrics dashboard."""
    today = date.today()
    locales = get_locales_by_visit(today - timedelta(days=30), today)

    return render(
        request,
        'dashboards/aggregated_metrics.html',
        {'locales_json': json.dumps(settings.SUMO_LANGUAGES),
         'locales': locales})


def _get_product(request):
    product_slug = request.GET.get('product')
    if product_slug:
        return get_object_or_404(Product, slug=product_slug)

    return None
