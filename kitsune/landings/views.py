from django.shortcuts import render

from mobility.decorators import mobile_template

from kitsune.products.models import Product
from kitsune.sumo.decorators import ssl_required
from kitsune.sumo.views import redirect_to
from kitsune.wiki.decorators import check_simple_wiki_locale


@check_simple_wiki_locale
def home(request):
    """The home page."""
    if request.MOBILE:
        return redirect_to(request, 'products', permanent=False)

    return render(request, 'landings/home.html', {
        'products': Product.objects.filter(visible=True)
    })


@ssl_required
@mobile_template('landings/{mobile/}get-involved.html')
def get_involved(request, template):
    return render(request, template)


@ssl_required
@mobile_template('landings/{mobile/}get-involved-questions.html')
def get_involved_questions(request, template):
    return render(request, template)


@ssl_required
@mobile_template('landings/{mobile/}get-involved-kb.html')
def get_involved_kb(request, template):
    return render(request, template)


@ssl_required
@mobile_template('landings/{mobile/}get-involved-l10n.html')
def get_involved_l10n(request, template):
    return render(request, template)


def integrity_check(request):
    return render(request, 'landings/integrity-check.html')
