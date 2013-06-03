from functools import wraps
import json
import time

from django.conf import settings
from django.http import HttpResponse, HttpResponseBadRequest

from products.models import Product
from wiki.models import Document


def serialize_document_for_offline(doc):
    """Grabs the document in a dictionary. This method returns a document that
    is ready to be inserted into the client-side database.
    """
    return {
        'key': doc.id,
        'title': doc.title,
        'summary': doc.current_revision.summary,
        'slug': doc.slug,
        'html': doc.html,
        'updated': int(time.mktime(doc.current_revision.created.timetuple())),
    }


def topics_key(locale, product, topic):
    return '{}~{}~{}'.format(locale, product, topic)


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

    docs = Document.objects.filter(products__id=product.id, locale=locale,
                                   is_archived=False, is_template=False)

    for doc in docs:
        if not doc.current_revision or not doc.html:
            # These documents don't have approved revision. We just skip them.
            continue

        serialized_doc = serialize_document_for_offline(doc)

        docs_bundle[serialized_doc['key']] = serialized_doc

        for t in doc.get_topics():
            key = topics_key(locale, product.slug, t.id)
            topic = topics.setdefault(key, {})
            if not topic:
                bundle['locales'][locale]['children'].add(key)
                topic['key'] = key
                topic['name'] = t.title
                topic['children'] = [topics_key(locale, product.slug, st.id) for st in t.subtopics.all()]
                topic['docs'] = []
                topic['product'] = product.slug
            topic['docs'].append(doc.id)


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

    if 'locales' in merged_bundle:
        merged_bundle['locales'] = merged_bundle['locales'].values()

    if 'topics' in merged_bundle:
        merged_bundle['topics'] = merged_bundle['topics'].values()

    if 'docs' in merged_bundle:
        merged_bundle['docs'] = merged_bundle['docs'].values()

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

    products = [Product.objects.get(slug=product) for product in products]

    bundles = []
    for locale in locales:
        for product in products:
            bundles.append(bundle_for_product(product, locale))

    data = json.dumps(merge_bundles(*bundles))

    return HttpResponse(data, mimetype='application/json')

@cors_enabled('*')
def get_languages(request):
    data = json.dumps({'languages': settings.LANGUAGE_CHOICES})

    return HttpResponse(data, mimetype='application/json')
