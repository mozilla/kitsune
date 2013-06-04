from functools import wraps
import json
import time

from django.conf import settings
from django.http import HttpResponse, HttpResponseBadRequest

from kitsune.products.models import Product
from kitsune.sumo.parser import _get_wiki_link
from kitsune.wiki.models import Document
from kitsune.wiki.parser import WikiParser as WParser

i = 0
def wiki_to_html(wiki_markup, locale=settings.WIKI_DEFAULT_LANGUAGE, doc_id=None):
    global i
    i += 1
    print i
    parsed = WikiParser(doc_id=doc_id).parse(wiki_markup, show_toc=False, locale=locale)
    return parsed

class WikiParser(WParser):
    def _hook_internal_link(self, parser, space, name):
        # This deserves refactoring with apps.sumo.parser.WikiParser._hook_internal_link
        # However, it is not yet the time to clean up everything.
        text = False
        title = name
        if '|' in name:
            title, text = title.split('|', 1)

        hash = ''
        if '#' in title:
            title, hash = title.split('#', 1)

        if hash != '':
            hash = '#' + hash.replace(' ', '_')

        if title == '' and hash != '':
            if not text:
                text = hash.replace('_', ' ')

            # This is modified as we don't want angular to clickjack.
            return u'<a href="{}" target="_self">{}</a>'.format(hash, text)

        link = _get_wiki_link(title, self.locale)
        extra_a_attr = ''
        if not link['found']:
            # This is modified too as when there is a not found link, we should
            # just return the text for offline.
            return text if text else link['text']

        if not text:
            text = link['text']

        return u'<a href="{url}{hash}">{text}</a>'.format(url=link['url'], hash=hash, text=text)

    def _hook_image_tag(self, parser, space, name):
        # TODO: obviously this gotta work better.
        params = {}
        if not '|' in name:
            title = name.strip()
            params['alt'] = title
        else:
            first = True
            for item in name.split('|'):
                if first:
                    title = item
                    first = False
                    continue
                item = item.strip()
                if '=' in item:
                    param, value = item.split('=', 1)
                    params[param] = value
                else:
                    params[item] = True
            # Let's not care about captions for now.

        if 'width' in params and 'height' in params:
            return '<div class="img-placeholder">{} x {} img placeholder</div>'
        else:
            return '<div class="img-placeholder">img placeholder</div>'

doc_key = lambda locale, doc_slug: locale + '~' + doc_slug
topic_key = lambda product_slug, topic_slug: product_slug + '~' + topic_slug

def serialize_document_for_offline(doc):
    """Grabs the document in a dictionary. This method returns a document that
    is ready to be inserted into the client-side database.
    """
    return {
        'key': doc_key(doc.locale, doc.slug),
        'title': doc.title,
        'summary': doc.current_revision.summary,
        'html': doc.html,
        #'html': wiki_to_html(doc.current_revision.content, locale=doc.locale, doc_id=doc.id),
        'updated': int(time.mktime(doc.current_revision.created.timetuple())),
        'slug': doc.slug
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

    docs = Document.objects.filter(products__id=product.id, locale=locale,
                                   is_archived=False, is_template=False)

    for doc in docs:
        if not doc.current_revision or not doc.html:
            # These documents don't have approved revision. We just skip them.
            continue

        serialized_doc = serialize_document_for_offline(doc)

        docs_bundle[serialized_doc['key']] = serialized_doc

        for t in doc.get_topics():
            topic = topics.setdefault(t.id, {})
            if not topic:
                bundle['locales'][locale]['children'].add(t.id)
                topic['key'] = topic_key(product.slug, t.slug)
                topic['name'] = t.title
                topic['children'] = [st.slug for st in t.subtopics.all()]
                topic['docs'] = []
                topic['product'] = product.slug # seems redundant with key, eh?
                topic['slug'] = t.slug
            topic['docs'].append(doc.slug)


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
