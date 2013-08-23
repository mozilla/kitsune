from hashlib import sha1
import json
import re
import time

from tower import ugettext as _

from django.conf import settings

from kitsune.offline.index import (
    TFIDFIndex,
    find_word_locations_with_spaces,
    find_word_locations_without_spaces
)
from kitsune.wiki.config import TROUBLESHOOTING_CATEGORY, HOW_TO_CATEGORY
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


def redis_bundle_name(locale, product_slug):
    return 'osumo:' + bundle_key(locale.lower(), product_slug.lower())


def transform_html(dochtml):
    """Transforms the html to something we want to serve in the app.

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

    # in order to save some space, the doc htmls and summaries are not returned
    # as archived articles are already out of date.
    if doc.is_archived:
        return {
            'key': doc_key(doc.locale, doc.slug),
            'title': doc.title,
            'archived': True,
            'slug': doc.slug
        }
    else:
        updated = int(time.mktime(doc.current_revision.created.timetuple()))
        return {
            'key': doc_key(doc.locale, doc.slug),
            'title': doc.title,
            'html': transform_html(doc.html),
            'updated': updated,
            'slug': doc.slug,
            'id': doc.id,
            'archived': False
        }


def bundle_for_product(product, locale):
    """Gets an entire bundle for a product in a locale."""
    bundle = {}

    # put a new locale into the database.
    bundle['locales'] = {}
    bundle['locales'][locale] = {
        'key': locale,
        'name': settings.LANGUAGES[locale.lower()],
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
        category__in=(TROUBLESHOOTING_CATEGORY, HOW_TO_CATEGORY)
    )

    # Since the any languages that are derived from English will not have a
    # product, we must find its parent's product.
    if locale == settings.WIKI_DEFAULT_LANGUAGE:
        docs = docs.filter(products__id=product.id)
    else:
        docs = docs.filter(parent__products__id=product.id)

    if locale in settings.LANGUAGES_WITHOUT_SPACES:
        find_word_locations = find_word_locations_without_spaces
    else:
        find_word_locations = find_word_locations_with_spaces

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
            index_builder.feed(doc.id, texts, find_word_locations)

        docs_bundle[serialized_doc['key']] = serialized_doc

        # Now we need to populate the topics for this locale.
        for t in doc.get_topics():
            if t.product.id == product.id:
                topic = topics.setdefault(t.slug, {})
                if not topic:  # this means that topics has not been set yet.
                    topic['key'] = topic_key(locale, product.slug, t.slug)
                    # The title of the document is not translated so we must
                    # use gettext to get the translation for it.
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
                    merged_locale['products'].extend(locale['products'])
                else:
                    merged_locale.update(locale)

        for key in ('topics', 'docs', 'indexes'):
            if key in bundle:
                merged_bundle.setdefault(key, {}).update(bundle[key])

    # This is because the database format is actually meant to have all of this
    # in a list format
    for key in ('locales', 'topics', 'docs', 'indexes'):
        if key in merged_bundle:
            merged_bundle[key] = merged_bundle[key].values()

    return merged_bundle


def insert_bundle_into_redis(redis, product, locale, bundle):
    """Put a bundle into redis.

    This is used in both the cron job and the view.
    """
    bundle = json.dumps(bundle)
    bundle_hash = sha1(bundle).hexdigest()  # track version

    name = redis_bundle_name(locale.lower(), product.lower())
    redis.hset(name, 'hash', bundle_hash)
    redis.hset(name, 'bundle', bundle)
    redis.hset(name, 'updated', time.time())

    return bundle, bundle_hash
