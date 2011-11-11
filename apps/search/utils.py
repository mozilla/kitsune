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

    # Reindex questions.
    import questions.es_search
    questions.es_search.reindex_questions()


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
