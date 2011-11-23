import elasticutils
import logging
import pyes
import time


ID_FACTOR = 100000
AGE_DIVISOR = 86400

# TODO: Is this the right thing to log to?
log = logging.getLogger('k.quetion.es_search')


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


def setup_mapping(index):
    from questions.models import Question

    # TODO: ES can infer types.  I don't know offhand if we can
    # provide some types and let it infer the rest.  If that's true,
    # then we can ditch all the defined types here except the strings
    # that need analysis.
    mapping = {
        'properties': {
            'id': {TYPE: LONG},
            'question_id': {TYPE: LONG},
            'title': {TYPE: STRING, INDEX: ANALYZED, ANALYZER: SNOWBALL},
            'question_content':
                {TYPE: STRING, INDEX: ANALYZED, ANALYZER: SNOWBALL,
                 STORE: YES, TERM_VECTOR: WITH_POS_OFFSETS},
            'answer_content':
                {TYPE: STRING, INDEX: ANALYZED, ANALYZER: SNOWBALL},
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
            'age': {TYPE: INTEGER},
            }
        }

    es = elasticutils.get_es()

    # TODO: If the mapping is there already and we do a put_mapping,
    # does that stomp on the existing mapping or raise an error?
    try:
        es.put_mapping(Question._meta.db_table, mapping, index)
    except pyes.exceptions.ElasticSearchException, e:
        log.error(e)


def _extract_question_data(question):
    d = {}

    d['question_id'] = question.id
    d['title'] = question.title
    d['question_content'] = question.content
    d['replies'] = question.num_answers
    d['is_solved'] = bool(question.solution_id)
    d['is_locked'] = question.is_locked
    d['has_answers'] = bool(question.num_answers)

    d['created'] = question.created
    d['updated'] = question.updated

    d['question_creator'] = question.creator.username
    d['question_votes'] = question.num_votes_past_week

    # TODO: This isn't going to work right.  When we do incremental
    # updates, then we'll be comparing question/answer with up-to-date
    # ages with question/answer with stale ages.  We need to either
    # change how this 'age' thing works or update all the documents
    # every 24 hours.  Keeping it here for now.
    if question.update is not None:
        updated_since_epoch = time.mktime(question.updated.timetuple())
        d['age'] = (time.time() - updated_since_epoch) / AGE_DIVISOR
    else:
        d['age'] = None

    return d


def _extract_answer(answer, question, question_data):
    d = {}

    d.update(question_data)

    d['id'] = (question.id * ID_FACTOR) + answer.id

    d['answer_content'] = answer.content
    d['has_helpful'] = bool(answer.num_helpful_votes)
    d['answer_creator'] = answer.creator.username
    d['answer_votes'] = answer.upvotes

    return d


def extract_question(question):
    """Extracts indexable attributes from a Question and its answers

    If the question has no answer, returns a list of one dict of the
    question data.

    If the question has answers, returns a list of one dict per
    answer.

    """
    question_data = _extract_question_data(question)

    if question.answers.count() == 0:
        # If this question has no answers, we fill out the answer
        # section as if it was a left outer join and then return that.

        # TODO: Some types can take a "null"--maybe it's better to do
        # that, but I don't know how that affects queries/filters/etc.
        question_data['id'] = question.id * ID_FACTOR
        question_data['answer_content'] = u''
        question_data['has_helpful'] = False
        question_data['answer_creator'] = u''
        question_data['answer_votes'] = 0
        return [question_data]

    # Build a list of answers with the question data and then return
    # that.
    ans_list = [_extract_answer(ans, question, question_data)
                for ans in question.answers.all()]

    return ans_list


def index_doc(doc, bulk=False, force_insert=False, es=None):
    from django.conf import settings
    from questions.models import Question

    if es is None:
        es = elasticutils.get_es()

    index = (settings.ES_INDEXES.get(Question._meta.db_table)
             or settings.ES_INDEXES['default'])

    try:
        es.index(doc, index, doc_type=Question._meta.db_table,
                 id=doc['id'], bulk=bulk, force_insert=force_insert)
    except pyes.urllib3.TimeoutError:
        # If we have a timeout, try it again rather than die.  If we
        # have a second one, that will cause everything to die.
        es.index(doc, index, doc_type=Question._meta.db_table,
                 id=doc['id'], bulk=bulk, force_insert=force_insert)


def index_docs(documents, bulk=False, force_insert=False, es=None):
    for doc in documents:
        index_doc(doc, bulk, force_insert, es)


# TODO: This is seriously intensive and takes a _long_ time to run.
# Need to reduce the work here.  This should not get called often.
def reindex_questions():
    """Updates the mapping and indexes all questions."""
    from questions.models import Question
    from django.conf import settings

    index = settings.ES_INDEXES['default']

    log.info('reindex questions: %s %s', index,
             Question._meta.db_table)

    es = pyes.ES(settings.ES_HOSTS, timeout=10.0)

    log.info('setting up mapping....')
    setup_mapping(index)

    log.info('iterating through questions....')
    total = Question.objects.count()
    t = 0
    for q in Question.objects.all():
        t += 1
        if t % 1000 == 0:
            log.info('%s/%s...', t, total)

        index_docs(extract_question(q), bulk=True, es=es)

    es.flush_bulk(forced=True)
    log.info('done!')
    es.refresh()
