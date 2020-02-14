from django.shortcuts import render


from kitsune.products.models import Product
from kitsune.sumo.decorators import ssl_required
from kitsune.wiki.decorators import check_simple_wiki_locale


@check_simple_wiki_locale
def home(request):
    """The home page."""
    return render(request, 'landings/home.html', {
        'products': Product.objects.filter(visible=True)
    })


@ssl_required
def get_involved(request):
    return render(request, 'landings/get-involved.html')


@ssl_required
def get_involved_questions(request):
    return render(request, 'landings/get-involved-questions.html')


@ssl_required
def get_involved_kb(request):
    return render(request, 'landings/get-involved-kb.html')


@ssl_required
def get_involved_l10n(request):
    return render(request, 'landings/get-involved-l10n.html')


def integrity_check(request):
    return render(request, 'landings/integrity-check.html')
