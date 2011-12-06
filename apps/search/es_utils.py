import elasticutils
import pprint
import pyes

from django.conf import settings


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
    """Returns the index for this model."""
    return (settings.ES_INDEXES.get(model._meta.db_table)
            or settings.ES_INDEXES['default'])


def es_reindex(percent=100):
    """Reindexes the database in Elastic.

    :arg percent: Defaults to 100.  Allows you to specify how much of
        each doctype you want to index.  This is useful for
        development where doing a full reindex takes an hour.
    """
    es = elasticutils.get_es()

    # Go through and delete, then recreate the indexes.
    for index in settings.ES_INDEXES.values():
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
    questions.es_search.reindex_questions(percent)

    # Reindex wiki documents.
    import wiki.es_search
    wiki.es_search.reindex_documents(percent)

    # Reindex forum posts.
    import forums.es_search
    forums.es_search.reindex_documents(percent)


def es_whazzup():
    """Runs cluster_stats on the Elastic system."""
    import elasticutils
    from forums.models import Post
    from questions.models import Question
    from wiki.models import Document

    # We create a logger because elasticutils uses it.
    import logging
    logging.basicConfig()

    es = elasticutils.get_es()

    pprint.pprint(es.cluster_stats())

    print 'Totals:'
    try:
        print 'total questions:', elasticutils.S(Question).count()
    except pyes.exceptions.IndexMissingException:
        print 'total questions: 0'
    try:
        print 'total forum posts:', elasticutils.S(Post).count()
    except pyes.exceptions.IndexMissingException:
        print 'total forum posts: 0'
    try:
        print 'total wiki docs:', elasticutils.S(Document).count()
    except pyes.exceptions.IndexMissingException:
        print 'total wiki docs: 0'
