from django import http
from django.conf import settings
from django.shortcuts import get_object_or_404

from kitsune.sumo.templatetags.jinja_helpers import urlparams
from kitsune.sumo.urlresolvers import reverse
from kitsune.wiki.models import Document

WIKI_URL_NAME_PREFIX = "wiki."


class WikiRoutingMiddleware:
    """
    Attempts to find the wiki document in the current locale,
    if it can't be found attempts to find its parent,
    and attempts to find it from there, redirecting if necessary.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_view(self, request, view_func, view_args, view_kwargs):
        url_name = request.resolver_match.url_name or ""
        document_slug = view_kwargs.get("document_slug")
        skip = getattr(view_func, "wiki_routing_skip", False)

        if url_name.startswith(WIKI_URL_NAME_PREFIX) and document_slug and not skip:
            locale = request.GET.get("locale", request.LANGUAGE_CODE)
            request.wiki_routing = {
                "doc_matches_locale": True,
            }
            try:
                request.wiki_routing["doc"] = Document.objects.get(
                    locale=locale, slug=document_slug
                )
            except Document.DoesNotExist:
                # Check if the document slug is available in default language.
                parent_doc = get_object_or_404(
                    Document, locale=settings.WIKI_DEFAULT_LANGUAGE, slug=document_slug
                )
                request.wiki_routing["doc"] = parent_doc
                request.wiki_routing["doc_matches_locale"] = False
                # If the document is available in the default language,
                # try fetching the localized version
                if translation := parent_doc.translated_to(locale):
                    request.wiki_routing["doc"] = translation
                    request.wiki_routing["doc_matches_locale"] = True
                    redirect = getattr(view_func, "wiki_routing_redirect", True)
                    if redirect:
                        url_name = request.resolver_match.url_name
                        url = reverse(url_name, args=[translation.slug], locale=locale)
                        url = urlparams(url, query_dict=request.GET)
                        return http.HttpResponseRedirect(url)
                else:
                    raise_404 = getattr(view_func, "wiki_routing_raise_404", True)
                    if raise_404:
                        raise http.Http404
