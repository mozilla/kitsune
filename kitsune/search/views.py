import logging
from datetime import datetime, timedelta

from django.shortcuts import render_to_response
from django.views.decorators.cache import cache_page

from kitsune.products.models import Product
from kitsune.wiki.facets import documents_for

log = logging.getLogger("k.search")


def cache_control(resp, cache_period):
    """Inserts cache/expires headers"""
    resp["Cache-Control"] = "max-age=%s" % (cache_period * 60)
    resp["Expires"] = (datetime.utcnow() + timedelta(minutes=cache_period)).strftime(
        "%A, %d %B %Y %H:%M:%S GMT"
    )
    return resp


@cache_page(60 * 60 * 168)  # 1 week.
def opensearch_plugin(request):
    """Render an OpenSearch Plugin."""
    host = "%s://%s" % ("https" if request.is_secure() else "http", request.get_host())

    # Use `render_to_response` here instead of `render` because `render`
    # includes the request in the context of the response. Requests
    # often include the session, which can include pickable things.
    # `render_to_respones` doesn't include the request in the context.
    return render_to_response(
        "search/plugin.html",
        {"host": host, "locale": request.LANGUAGE_CODE},
        content_type="application/opensearchdescription+xml",
    )


def _fallback_results(locale, product_slugs):
    """Return the top 20 articles by votes for the given product(s)."""
    products = []
    for slug in product_slugs:
        try:
            p = Product.objects.get(slug=slug)
            products.append(p)
        except Product.DoesNotExist:
            pass

    docs, fallback = documents_for(locale, products=products)
    docs = docs + (fallback or [])

    return docs[:20]
