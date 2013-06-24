from functools import wraps
import re
import time

from tower import ugettext as _

from django.conf import settings
from django.http import HttpResponse, HttpResponseBadRequest

from kitsune.offline.index import TFIDFIndex, find_word_locations_with_spaces
from kitsune.wiki.config import CATEGORIES
from kitsune.wiki.models import Document


_noscript_regex = re.compile(r'<noscript>.*?</noscript>', flags=re.DOTALL)


def bundle_key(locale, product_slug):
    """The key for a bundle as stored in client-side's indexeddb.

    The arguments to this function must be strings. This key is used
    for the index.
    """
    return locale + '~' + product_slug


def doc_key(locale, doc_slug):
    """The key for a document as stored in client-side's indexeddb.

    The arguments to this function must be strings.
    """
    return locale + '~' + doc_slug


def topic_key(locale, product_slug, topic_slug):
    """The key for a topic as stored in client-side's indexeddb.

    The arguments to this function must be strings.
    """
    return locale + '~' + product_slug + '~' + topic_slug


def transform_html(dochtml):
    """

    Do things to the document html such as stripping out things the
    offline app do not need. We could also do this in WikiParser,
    but this is probably easier for now.
    """
    # Strip out all the <noscript> images
    dochtml = _noscript_regex.sub('', dochtml)

    return dochtml


def serialize_document_for_offline(doc):
    """Grabs the document in a dictionary.

    This method returns a document that is ready to be inserted into
    the client-side database.
    """
    if doc.is_archived:
        return {
            'key': doc_key(doc.locale, doc.slug),
            'title': doc.title,
            'archived': True,
            'slug': doc.slug
        }
    else:
        # Note that we don't need 'archived' here as in JavaScript,
        # doc.archived will return undefined.
        updated = int(time.mktime(doc.current_revision.created.timetuple()))
        return {
            'key': doc_key(doc.locale, doc.slug),
            'title': doc.title,
            'html': transform_html(doc.html),
            'updated': updated,
            'slug': doc.slug,
            'id': doc.id
        }


def bundle_for_product(product, locale):
    """Gets an entire bundle for a product in a locale.
    """
    bundle = {}

    # put a new locale into the database.
    bundle['locales'] = {}
    bundle['locales'][locale] = {
        'key': locale,
        'name': settings.LANGUAGES[locale.lower()],
        'children': set(),
        'products': [{'slug': product.slug, 'name': product.title}]
    }

    # we need a dictionary as we need to merge everything together.
    bundle['topics'] = topics = {}
    bundle['docs'] = docs_bundle = {}
    bundle['indexes'] = {}

    index_builder = TFIDFIndex()

    docs = Document.objects.filter(
        locale=locale,
        is_template=False,
        category__in=(CATEGORIES[0][0], CATEGORIES[1][0])
    )

    # Since the any languages that are derived from English will not have a
    # product, we must find its parent's product.
    if locale == settings.WIKI_DEFAULT_LANGUAGE:
        docs = docs.filter(products__id=product.id)
    else:
        docs = docs.filter(parent__products__id=product.id)

    for doc in docs:
        if not doc.current_revision or not doc.html or doc.redirect_url():
            # These documents don't have approved revision. We just skip them.
            # or if it is a redirect.. why even bother.
            continue

        serialized_doc = serialize_document_for_offline(doc)

        # Only non-archived documents need to be indexed.
        if not doc.is_archived:
            # We only index the title and the summary as otherwise the corpus
            # is too big. We also boost the score of the title.
            texts = [(doc.title, 1.2), (doc.current_revision.summary, 1)]
            # TODO: use find_word_locations_without_spaces if it is an east
            # asian language
            find_word_locations = find_word_locations_with_spaces
            index_builder.feed(doc.id, texts, find_word_locations)

        docs_bundle[serialized_doc['key']] = serialized_doc

        # Now we need to populate the topics for this locale.
        for t in doc.get_topics():
            topic = topics.setdefault(t.slug, {})
            if not topic:  # this means that topics has not been set yet.
                bundle['locales'][locale]['children'].add(t.slug)
                topic['key'] = topic_key(locale, product.slug, t.slug)
                # The title of the document is not translated so we must use
                # gettext to get the translation for it.
                topic['name'] = _(t.title)
                topic['children'] = [st.slug for st in t.subtopics.all()]
                topic['docs'] = []
                topic['product'] = product.slug
                topic['slug'] = t.slug
            topic['docs'].append(doc.slug)

    # The bundle needs an index!
    bundlekey = bundle_key(locale, product.slug)
    bundle['indexes'][bundlekey] = {}
    bundle['indexes'][bundlekey]['key'] = bundlekey
    # The client side will search through this index.
    bundle['indexes'][bundlekey]['index'] = index_builder.offline_index()

    # Note that we were using a set. Must convert it to a list for JSON to
    # understand.
    bundle['locales'][locale]['children'] = list(
        bundle['locales'][locale]['children']
    )

    return bundle


def merge_bundles(*bundles):
    """Merges multiple bundles generated by bundle_for_product into one.
    """
    merged_bundle = {}
    for bundle in bundles:
        if 'locales' in bundle:
            merged_locales = merged_bundle.setdefault('locales', {})
            for k, locale in bundle['locales'].iteritems():
                merged_locale = merged_locales.setdefault(k, {})
                if merged_locale:
                    merged_locale['children'].extend(locale['children'])
                    merged_locale['products'].extend(locale['products'])
                else:
                    merged_locale.update(locale)

        if 'topics' in bundle:
            merged_bundle.setdefault('topics', {}).update(bundle['topics'])

        if 'docs' in bundle:
            merged_bundle.setdefault('docs', {}).update(bundle['docs'])

        if 'indexes' in bundle:
            merged_bundle.setdefault('indexes', {}).update(bundle['indexes'])

    # This is because the database format is actually meant to have all of this
    # in a list format
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
    """A simple decorator to enable CORS.
    """
    def decorator(f):
        @wraps(f)
        def decorated_func(request, *args, **kwargs):
            if request.method == 'OPTIONS':
                # preflight
                if ('HTTP_ACCESS_CONTROL_REQUEST_METHOD' in request.META and
                    'HTTP_ACCESS_CONTROL_REQUEST_HEADERS' in request.META):

                    response = HttpResponse()
                    response['Access-Control-Allow-Methods'] = ", ".join(
                        methods)

                    # TODO: We might need to change this
                    response['Access-Control-Allow-Headers'] = \
                        request.META['HTTP_ACCESS_CONTROL_REQUEST_HEADERS']
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
