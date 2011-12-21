import elasticutils
import logging
import pyes
import time

from search.es_utils import (TYPE, LONG, INDEX, STRING, ANALYZED, ANALYZER,
                             SNOWBALL, TERM_VECTOR, STORE, YES, BOOLEAN,
                             WITH_POS_OFFSETS, DATE, INTEGER, get_index)


log = logging.getLogger('k.questions.es_search')


def setup_mapping(index):
    from questions.models import Question

    mapping = {
        'properties': {
            'id': {TYPE: LONG},
            'question_id': {TYPE: LONG},
            'title': {TYPE: STRING, ANALYZER: SNOWBALL},
            'question_content':
                {TYPE: STRING, ANALYZER: SNOWBALL,
                # TODO: Stored because originally, this is the only field we
                # were excerpting on. Standardize one way or the other.
                 STORE: YES, TERM_VECTOR: WITH_POS_OFFSETS},
            'answer_content':
                {TYPE: STRING, ANALYZER: SNOWBALL},
            'replies': {TYPE: INTEGER},
            'is_solved': {TYPE: BOOLEAN},
            'is_locked': {TYPE: BOOLEAN},
            'has_answers': {TYPE: BOOLEAN},
            'has_helpful': {TYPE: BOOLEAN},
            'created': {TYPE: DATE},
            'updated': {TYPE: DATE},
            'question_creator': {TYPE: STRING},
            'answer_creator': {TYPE: STRING},
            'question_votes': {TYPE: INTEGER},
            'answer_votes': {TYPE: INTEGER},
            }
        }

    es = elasticutils.get_es()

    # TODO: If the mapping is there already and we do a put_mapping,
    # does that stomp on the existing mapping or raise an error?
    try:
        es.put_mapping(Question._meta.db_table, mapping, index)
    except pyes.exceptions.ElasticSearchException, e:
        log.error(e)


def extract_question(question):
    """Extracts indexable attributes from a Question and its answers."""
    question_data = {}

    question_data['id'] = question.id

    question_data['title'] = question.title
    question_data['question_content'] = question.content
    question_data['replies'] = question.num_answers
    question_data['is_solved'] = bool(question.solution_id)
    question_data['is_locked'] = question.is_locked
    question_data['has_answers'] = bool(question.num_answers)

    question_data['created'] = question.created
    question_data['updated'] = question.updated

    question_data['question_creator'] = question.creator.username
    question_data['question_votes'] = question.num_votes_past_week

    # answer_content is a \n\n delimited mish-mosh of all the
    # answer content.
    answer_content = []

    # has_helpful is true if at least one answer is marked as
    # helpful.
    has_helpful = False

    # answer_creator is the set of all answer creator user names.
    answer_creator = set()

    # answer_votes is the sum of votes for all of the answers.
    answer_votes = 0

    for ans in question.answers.all():
        answer_content.append(ans.content)
        has_helpful = has_helpful or bool(ans.num_helpful_votes)
        answer_creator.add(ans.creator.username)
        answer_votes += ans.upvotes

    question_data['answer_content'] = '\n\n'.join(answer_content)
    question_data['has_helpful'] = has_helpful
    question_data['answer_creator'] = list(answer_creator)
    question_data['answer_votes'] = answer_votes

    return question_data


def index_doc(doc, bulk=False, force_insert=False, es=None):
    from questions.models import Question

    if es is None:
        es = elasticutils.get_es()

    index = get_index(Question)

    try:
        es.index(doc, index, doc_type=Question._meta.db_table,
                 id=doc['id'], bulk=bulk, force_insert=force_insert)
    except pyes.urllib3.TimeoutError:
        # If we have a timeout, try it again rather than die.  If we
        # have a second one, that will cause everything to die.
        es.index(doc, index, doc_type=Question._meta.db_table,
                 id=doc['id'], bulk=bulk, force_insert=force_insert)


def unindex_questions(ids):
    """Removes Questions from the index."""
    from questions.models import Question

    es = elasticutils.get_es()
    index = get_index(Question)

    for question_id in ids:
        # TODO wrap this in a try/except--amongst other things, this will
        # only be in the index if the Question had no Answers.
        try:
            es.delete(index, doc_type=Question._meta.db_table,
                      id=question_id)
        except pyes.exceptions.NotFoundException:
            # If the document isn't in the index, then we ignore it.
            # TODO: Is that right?
            pass


def unindex_answers(ids):
    """Removes Answers from the index.

    :arg ids: list of question ids

    """
    # Answers are rolled up in Question documents, so we reindex the
    # Question.
    from questions.models import Question

    for question_id in ids:
        try:
            # TODO: test the case where we delete the question
            # twice.
            question = Question.objects.get(id=question_id)
            index_doc(extract_question(question))
        except Question.ObjectDoesNotExist:
            pass


def reindex_questions(percent=100):
    """Iterate over this to update the mapping and index all documents.

    Yields number of documents done.

    Note: This gets run from the command line, so we log stuff to let
    the user know what's going on.

    :arg percent: The percentage of questions to index.  Defaults to
        100--e.g. all of them.

    """
    from questions.models import Question
    from django.conf import settings

    index = get_index(Question)

    start_time = time.time()

    log.info('reindex questions: %s %s', index,
             Question._meta.db_table)

    es = pyes.ES(settings.ES_HOSTS, timeout=10.0)

    log.info('setting up mapping....')
    setup_mapping(index)

    log.info('iterating through questions....')
    total = Question.objects.count()
    to_index = int(total * (percent / 100.0))
    log.info('total questions: %s (to be indexed: %s)', total, to_index)
    total = to_index

    t = 0
    for q in Question.objects.order_by('id').all():
        t += 1
        if t % 1000 == 0:
            time_to_go = (total - t) * ((time.time() - start_time) / t)
            if time_to_go < 60:
                time_to_go = "%d secs" % time_to_go
            else:
                time_to_go = "%d min" % (time_to_go / 60)
            log.info('%s/%s...  (%s to go)', t, total, time_to_go)
            es.flush_bulk(forced=True)

        if t > total:
            break

        index_doc(extract_question(q), bulk=True, es=es)
        yield t

    es.flush_bulk(forced=True)
    log.info('done!')
    es.refresh()
