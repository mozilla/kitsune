from django.conf import settings


def get_index_name(index_name):
    name_format = "{prefix}_{suffix}"
    name = name_format.format(prefix=settings.ES_INDEX_PREFIX, suffix=index_name)
    return name


ES_SYNONYM_LOCALES = [
    'en-US',
]

WIKI_DOCUMENT_INDEX_NAME = get_index_name('wiki_document')
QUESTION_INDEX_NAME = get_index_name('question')
USER_INDEX_NAME = get_index_name('user')

INDEX_ALIAS_FORMAT = "{index_name}_{suffix}"

NON_ANALYZER_LOCALE_INDEX = 'general'
