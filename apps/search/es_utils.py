import os
import elasticutils
import pprint
import pyes

from django.conf import settings


# TODO: Make this less silly.  I do this because if I typo a name,
# pyflakes points it out, but if I typo a string, it doesn't notice
# and typos are always kicking my ass.

TYPE = 'type'
ANALYZER = 'analyzer'
INDEX = 'index'
STORE = 'store'
TERM_VECTOR = 'term_vector'

LONG = 'long'
INTEGER = 'integer'
STRING = 'string'
BOOLEAN = 'boolean'
DATE = 'date'

ANALYZED = 'analyzed'

SNOWBALL = 'snowball'

YES = 'yes'

WITH_POS_OFFSETS = 'with_positions_offsets'


def get_index(model):
    """Returns the index for this model.

    Takes into account whether we're testing or not.
    """
    if os.environ.get('DJANGO_ENVIRONMENT') == 'test':
        index_dict = settings.TEST_ES_INDEXES
    else:
        index_dict = settings.ES_INDEXES

    return index_dict.get(model._meta.db_table) or index_dict['default']


def es_reindex():
    """Reindexes the database in Elastic."""
    es = elasticutils.get_es()

    if os.environ.get('DJANGO_ENVIRONMENT') == 'test':
        index_dict = settings.TEST_ES_INDEXES
    else:
        index_dict = settings.ES_INDEXES

    # Go through and delete, then recreate the indexes.
    for index in index_dict.values():
        es.delete_index_if_exists(index)

        try:
            es.create_index_if_missing(index)
        except pyes.exceptions.ElasticSearchException:
            # TODO: Why would this throw an exception?  We should handle
            # it.  Maybe Elastic isn't running or something in which case
            # proceeding is an exercise in futility.
            pass

    # Reindex questions.
    import questions.es_search
    questions.es_search.reindex_questions()

    # Reindex wiki documents.
    import wiki.es_search
    wiki.es_search.reindex_documents()

    # Reindex forum posts.
    import forums.es_search
    forums.es_search.reindex_documents()


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
        indices="questions_question")["count"]
    print "forums docs count:", es.count(
        pyes.WildcardQuery('title', '*'),
        indices="forums_post")["count"]
    print "wiki docs count:", es.count(
        pyes.WildcardQuery('title', '*'),
        indices="wiki_document")["count"]
