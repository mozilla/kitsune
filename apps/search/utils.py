import pprint
import subprocess
import zlib

import bleach

from django.conf import settings

from sumo_locales import LOCALES


crc32 = lambda x: zlib.crc32(x.encode('utf-8')) & 0xffffffff


call = lambda x: subprocess.Popen(x, stdout=subprocess.PIPE).communicate()


def clean_excerpt(excerpt):
    return bleach.clean(excerpt)


def reindex(rotate=False):
    """Reindex sphinx.

    Note this is only to be used in dev and test environments.

    """
    calls = [settings.SPHINX_INDEXER, '--all', '--config',
             settings.SPHINX_CONFIG_PATH]
    if rotate:
        calls.append('--rotate')

    call(calls)


def es_reindex():
    """Reindexes the database in Elastic."""

    import elasticutils
    import pyes

    es = elasticutils.get_es()

    # TODO: unhardcode this
    es.delete_index("sumo")

    try:
        es.create_index_if_missing("sumo")
    except pyes.exceptions.ElasticSearchException:
        # TODO: Why would this throw an exception?  We should handle
        # it.  Maybe Elastic isn't running or something in which case
        # proceeding is an exercise in futility.
        pass

    # Reindex questions.
    import questions.es_search
    questions.es_search.reindex_questions()


def es_whazzup():
    """Runs cluster_stats on the Elastic system."""
    import elasticutils
    import pyes

    es = elasticutils.get_es()

    pprint.pprint(es.cluster_stats())

    # This is goofy, but it gives us a count of all the question
    # documents in the index.
    print "questions docs count:", es.count(
        pyes.WildcardQuery('title', '*'),
        indices="questions")["count"]


def start_sphinx():
    """Start sphinx.

    Note this is only to be used in dev and test environments.

    """
    call([settings.SPHINX_SEARCHD, '--config',
        settings.SPHINX_CONFIG_PATH])


def stop_sphinx():
    """Stop sphinx.

    Note this is only to be used in dev and test environments.

    """
    call([settings.SPHINX_SEARCHD, '--stop', '--config',
        settings.SPHINX_CONFIG_PATH])


def locale_or_default(locale):
    """Return `locale` or, if `locale` isn't a known locale, a default.

    Default is taken from Django's LANGUAGE_CODE setting.

    """
    if locale not in LOCALES:
        locale = settings.LANGUAGE_CODE
    return locale
