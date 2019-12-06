from django.conf import settings


##################################
# ElasticSearch v1 configuration #
##################################

ES_SYNONYM_LOCALES = [
    'en-US',
]

##################################
# ElasticSearch v2 configuration #
##################################


def get_index_name(index_name):
    name_format = "{prefix}_{suffix}"
    name = name_format.format(prefix=settings.ES_INDEX_PREFIX, suffix=index_name)
    return name


WIKI_DOCUMENT_INDEX_NAME = get_index_name('kb_index')
QUESTION_INDEX_NAME = get_index_name('aaq_index')
USER_INDEX_NAME = get_index_name('user_index')

ES_LOCALE_ANALYZERS = {
    'ar': 'arabic',
    'bg': 'bulgarian',
    'cs': 'czech',
    'fa': 'persian',
    'hi-IN': 'hindi',
    'id': 'indonesian',
    'ja': 'cjk',
    'pl': 'polish',
    'th': 'thai',
    'zh-CN': 'chinese',
    'zh-TW': 'chinese',
}

# Locales that uses snowball tokenizer
ES_SNOWBALL_LOCALES = {
    'eu': 'Basque',
    'ca': 'Catalan',
    'da': 'Danish',
    'nl': 'Dutch',
    'en-US': 'English',
    'fi': 'Finnish',
    'fr': 'French',
    'de': 'German',
    'hu': 'Hungarian',
    'it': 'Italian',
    'no': 'Norwegian',
    'pt-BR': 'Portuguese',
    'pt-PT': 'Portuguese',
    'ro': 'Romanian',
    'ru': 'Russian',
    'es': 'Spanish',
    'sv': 'Swedish',
    'tr': 'Turkish',
}

DEFAULT_ES7_CONNECTION = 'es7_default'
