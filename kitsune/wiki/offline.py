from functools import wraps
import json
import time

from tower import ugettext as _

from django.conf import settings
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseNotFound

from kitsune.products.models import Product
from kitsune.sumo.utils import uselocale
from kitsune.sumo.parser import _get_wiki_link
from kitsune.wiki.config import CATEGORIES
from kitsune.wiki.models import Document
from kitsune.wiki.parser import WikiParser as WParser
from kitsune.wiki.tfidf import TFIDFAnalysis, find_word_locations_en_like


bundle_key = lambda locale, product_slug: locale + '~' + product_slug
doc_key = lambda locale, doc_slug: locale + '~' + doc_slug
topic_key = lambda locale, product_slug, topic_slug: locale + '~' + product_slug + '~' + topic_slug

def serialize_document_for_offline(doc):
    """Grabs the document in a dictionary. This method returns a document that
    is ready to be inserted into the client-side database.
    """
    if doc.is_archived:
        return {
            'key': doc_key(doc.locale, doc.slug),
            'title': doc.title,
            'archived': True,
        }
    else:
        return {
            'key': doc_key(doc.locale, doc.slug),
            'title': doc.title,
            'html': doc.html,
            #'html': wiki_to_html(doc.current_revision.content, locale=doc.locale, doc_id=doc.id),
            'updated': int(time.mktime(doc.current_revision.created.timetuple())),
            'slug': doc.slug,
            'archived': False,
            'id': doc.id
        }


def bundle_for_product(product, locale):
    """Gets an entire bundle for a product in a locale.
    """
    bundle = {};
    bundle['locales'] = {};
    bundle['locales'][locale] = {
        'key': locale,
        'name': settings.LANGUAGES[locale.lower()],
        'children': set(),
        'products': [{'slug': product.slug, 'name': product.title}]
    }

    # we need a dictionary as we need to merge everything together.
    bundle['topics'] = topics = {}
    bundle['docs'] = docs_bundle = {}
    bundle['indexes'] = indexes = {}

    index_builder = TFIDFAnalysis()

    if locale == settings.WIKI_DEFAULT_LANGUAGE:
        docs = Document.objects.filter(products__id=product.id, locale=locale,
                                       is_template=False,
                                       category__in=(CATEGORIES[0][0],
                                                     CATEGORIES[1][0]))
    else:
        docs = Document.objects.filter(parent__products__id=product.id,
                                       locale=locale, is_template=False,
                                       category__in=(CATEGORIES[0][0],
                                                     CATEGORIES[1][0]))

    for doc in docs:
        if not doc.current_revision or not doc.html or doc.redirect_url():
            # These documents don't have approved revision. We just skip them.
            # or if it is a redirect.. why even bother.
            continue

        serialized_doc = serialize_document_for_offline(doc)

        if not doc.is_archived:
            index_builder.feed(doc.id, [(doc.title, 1.2), (doc.current_revision.summary, 1)], find_word_locations_en_like)

        docs_bundle[serialized_doc['key']] = serialized_doc

        for t in doc.get_topics():
            topic = topics.setdefault(t.id, {})
            if not topic:
                bundle['locales'][locale]['children'].add(t.slug)
                topic['key'] = topic_key(locale, product.slug, t.slug)
                topic['name'] = _(t.title)
                topic['children'] = [st.slug for st in t.subtopics.all()]
                topic['docs'] = []
                topic['product'] = product.slug # seems redundant with key, eh?
                topic['slug'] = t.slug
            topic['docs'].append(doc.slug)


    index_builder.done = True
    bundlekey = bundle_key(locale, product.slug)
    bundle['indexes'][bundlekey] = {}
    bundle['indexes'][bundlekey]['key'] = bundlekey
    bundle['indexes'][bundlekey]['index'] = index_builder.offline_index()

    bundle['locales'][locale]['children'] = list(bundle['locales'][locale]['children'])
    return bundle


def merge_bundles(*bundles):
    merged_bundle = {}
    for bundle in bundles:
        if 'locales' in bundle:
            locales = merged_bundle.setdefault('locales', {})
            for k, locale in bundle['locales'].iteritems():
                l = locales.setdefault(k, {})
                if l:
                    l['children'].extend(locale['children'])
                    l['products'].extend(locale['products'])
                else:
                    l.update(locale)

        if 'topics' in bundle:
            merged_bundle.setdefault('topics', {}).update(bundle['topics'])

        if 'docs' in bundle:
            merged_bundle.setdefault('docs', {}).update(bundle['docs'])

        if 'indexes' in bundle:
            merged_bundle.setdefault('indexes', {}).update(bundle['indexes'])

    if 'locales' in merged_bundle:
        merged_bundle['locales'] = merged_bundle['locales'].values()

    if 'topics' in merged_bundle:
        merged_bundle['topics'] = merged_bundle['topics'].values()

    if 'docs' in merged_bundle:
        merged_bundle['docs'] = merged_bundle['docs'].values()

    if 'indexes' in merged_bundle:
        merged_bundle['indexes'] = merged_bundle['indexes'].values()

    return merged_bundle


def cors_enabled(origin, methods=['GET']):
    def decorator(f):
        @wraps(f)
        def decorated_func(request, *args, **kwargs):
            if request.method == 'OPTIONS':
                # preflight
                if 'HTTP_ACCESS_CONTROL_REQUEST_METHOD' in request.META and 'HTTP_ACCESS_CONTROL_REQUEST_HEADERS' in request.META:
                    response = HttpResponse()
                    response['Access-Control-Allow-Methods'] = ", ".join(methods)
                    # TODO: We might need to change this
                    response['Access-Control-Allow-Headers'] = request.META['HTTP_ACCESS_CONTROL_REQUEST_HEADERS']
                else:
                    return HttpResponseBadRequest()
            elif request.method in methods:
                response = f(request, *args, **kwargs)
            else:
                return HttpResponseBadRequest()

            response['Access-Control-Allow-Origin'] = origin
            return response
        return decorated_func
    return decorator

@cors_enabled('*')
def get_bundles(request):
    if 'locales' not in request.GET or 'products' not in request.GET:
        return HttpResponseBadRequest()

    locales = request.GET.getlist('locales', [])
    products = request.GET.getlist('products', [])

    try:
        products = [Product.objects.get(slug=product) for product in products]
    except Product.DoesNotExist:
        return HttpResponseNotFound('{"error": "not found", "reason": "invalid product"}', mimetype='application/json')

    bundles = []
    for locale in locales:
        if locale.lower() not in settings.LANGUAGES:
            return HttpResponseNotFound('{"error": "not found", "reason": "invalid locale"}', mimetype='application/json')

        for product in products:
            with uselocale(locale):
                bundles.append(bundle_for_product(product, locale))

    data = json.dumps(merge_bundles(*bundles))

    return HttpResponse(data, mimetype='application/json')

@cors_enabled('*')
def get_languages(request):
    data = json.dumps({'languages': settings.LANGUAGE_CHOICES})

    return HttpResponse(data, mimetype='application/json')

