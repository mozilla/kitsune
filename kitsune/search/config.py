from django.conf import settings


def get_index_name(index_name):
    name_format = "{prefix}_{suffix}"
    name = name_format.format(prefix=settings.ES_INDEX_PREFIX, suffix=index_name)
    return name


ES_SYNONYM_LOCALES = [
    "en-US",
]

WIKI_DOCUMENT_INDEX_NAME = get_index_name("wiki_document")
QUESTION_INDEX_NAME = get_index_name("question")
USER_INDEX_NAME = get_index_name("user")
FORUM_THREAD_INDEX_NAME = get_index_name("forum_thread")

ES_LOCALE_ANALYZERS = {
    "ar": "arabic",
    "bg": "bulgarian",
    "cs": "czech",
    "fa": "persian",
    "hi-IN": "hindi",
    "id": "indonesian",
    "ja": "cjk",
    "pl": "polish",
    "th": "thai",
    "zh-CN": "chinese",
    "zh-TW": "chinese",
}

# Locales that uses snowball tokenizer
ES_SNOWBALL_LOCALES = {
    "eu": "Basque",
    "ca": "Catalan",
    "da": "Danish",
    "nl": "Dutch",
    "en-US": "English",
    "fi": "Finnish",
    "fr": "French",
    "de": "German",
    "hu": "Hungarian",
    "it": "Italian",
    "no": "Norwegian",
    "pt-BR": "Portuguese",
    "pt-PT": "Portuguese",
    "ro": "Romanian",
    "ru": "Russian",
    "es": "Spanish",
    "sv": "Swedish",
    "tr": "Turkish",
}

DEFAULT_ES7_CONNECTION = "es7_default"
