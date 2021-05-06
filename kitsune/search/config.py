ES_SYNONYM_LOCALES = [
    "en-US",
]

# number of times to retry updates if a conflict happens before raising
UPDATE_RETRY_ON_CONFLICT = 2

# these are "synonyms" we need to define as mappings because they contain stop words
ES_MAPPINGS = [
    "add-on => addon",
    "add on => addon",
    "plug-in => plugin",
    "plug in => plugin",
    "sign-in => signin",
    "sign in => signin",
    "signed in => signin",
    "log-in => login",
    "log in => login",
    "logged in => login",
]

ES_DEFAULT_ANALYZER_NAME = "default_sumo"
ES_DEFAULT_ANALYZER = {
    "tokenizer": "standard",
    "filter": ["lowercase", "stop"],
    "char_filter": [
        "html_strip",
        {"type": "mapping", "mappings": ES_MAPPINGS},
    ],
}

ES_ALL_SYNONYMS_NAME = "_all"

# by and large copied from
# https://www.elastic.co/guide/en/elasticsearch/reference/7.10/analysis-lang-analyzer.html
# NB: boolean filter arguments should be specified as a string, i.e. `"true"` rather than `True`,
# explained here: https://github.com/mozilla/sumo-project/issues/719#issuecomment-754677048
ES_LOCALE_ANALYZERS = {
    "ar": {
        "filter": [
            "lowercase",
            "decimal_digit",
            {"type": "stop", "stopwords": "_arabic_"},
            "arabic_normalization",
            {"type": "stemmer", "language": "arabic"},
        ]
    },
    "bg": {
        "filter": [
            "lowercase",
            {"type": "stop", "stopwords": "_bulgarian_"},
            {"type": "stemmer", "language": "bulgarian"},
        ]
    },
    "bn": {
        "filter": [
            "lowercase",
            "decimal_digit",
            "indic_normalization",
            "bengali_normalization",
            {"type": "stop", "stopwords": "_bengali_"},
            {"type": "stemmer", "language": "bengali"},
        ]
    },
    "ca": {
        "filter": [
            {
                "type": "elision",
                "articles": ["d", "l", "m", "n", "s", "t"],
                "articles_case": "true",
            },
            "lowercase",
            {"type": "stop", "stopwords": "_catalan_"},
            {"type": "stemmer", "language": "catalan"},
        ]
    },
    "cs": {
        "filter": [
            "lowercase",
            {"type": "stop", "stopwords": "_czech_"},
            {"type": "stemmer", "language": "czech"},
        ]
    },
    "da": {
        "filter": [
            "lowercase",
            {"type": "stop", "stopwords": "_danish_"},
            {"type": "stop", "stopwords": "_danish_"},
        ]
    },
    "de": {
        "filter": [
            "lowercase",
            {"type": "stop", "stopwords": "_german_"},
            "german_normalization",
            {"type": "stemmer", "language": "light_german"},
        ]
    },
    "el": {
        "filter": [
            {"type": "lowercase", "language": "greek"},
            {"type": "stop", "stopwords": "_greek_"},
            {"type": "stemmer", "language": "greek"},
        ]
    },
    "en-US": {
        "filter": [
            {"type": "stemmer", "language": "possessive_english"},
            "lowercase",
            {"type": "stop", "stopwords": "_english_"},
            {"type": "stemmer", "language": "english"},
        ]
    },
    "es": {
        "filter": [
            "lowercase",
            {"type": "stop", "stopwords": "_spanish_"},
            {"type": "stemmer", "language": "light_spanish"},
        ]
    },
    "et": {
        "filter": [
            "lowercase",
            {"type": "stop", "stopwords": "_estonian_"},
            {"type": "stemmer", "language": "estonian"},
        ]
    },
    "eu": {
        "filter": [
            "lowercase",
            {"type": "stop", "stopwords": "_basque_"},
            {"type": "stemmer", "language": "basque"},
        ]
    },
    "fa": {
        "filter": [
            "lowercase",
            "decimal_digit",
            "arabic_normalization",
            "persian_normalization",
            {"type": "stop", "stopwords": "_persian_"},
        ],
        "char_filter": [
            {"type": "mapping", "mappings": ["\\u200C=>\\u0020"]},
            "html_strip",
            {"type": "mapping", "mappings": ES_MAPPINGS},
        ],
    },
    "fi": {
        "filter": [
            "lowercase",
            {"type": "stop", "stopwords": "_finnish_"},
            {"type": "stemmer", "language": "finnish"},
        ]
    },
    "fr": {
        "filter": [
            {
                "type": "elision",
                "articles_case": "true",
                "articles": [
                    "l",
                    "m",
                    "t",
                    "qu",
                    "n",
                    "s",
                    "j",
                    "d",
                    "c",
                    "jusqu",
                    "quoiqu",
                    "lorsqu",
                    "puisqu",
                ],
            },
            "lowercase",
            {"type": "stop", "stopwords": "_french_"},
            {"type": "stemmer", "language": "light_french"},
        ]
    },
    "ga-IE": {
        "filter": [
            {"type": "stop", "stopwords": ["h", "n", "t"], "ignore_case": "true"},
            {"type": "elision", "articles": ["d", "m", "b"], "articles_case": "true"},
            {"type": "lowercase", "language": "irish"},
            {"type": "stop", "stopwords": "_irish_"},
            {"type": "stemmer", "language": "irish"},
        ]
    },
    "gl": {
        "filter": [
            "lowercase",
            {"type": "stop", "stopwords": "_galician_"},
            {"type": "stemmer", "language": "galician"},
        ]
    },
    "hi-IN": {
        "filter": [
            "lowercase",
            "decimal_digit",
            "indic_normalization",
            "hindi_normalization",
            {"type": "stop", "stopwords": "_hindi_"},
            {"type": "stemmer", "language": "hindi"},
        ]
    },
    "hu": {
        "filter": [
            "lowercase",
            {"type": "stop", "stopwords": "_hungarian_"},
            {"type": "stemmer", "language": "hungarian"},
        ]
    },
    "id": {
        "filter": [
            "lowercase",
            {"type": "stop", "stopwords": "_indonesian_"},
            {"type": "stemmer", "language": "indonesian"},
        ]
    },
    "it": {
        "filter": [
            {
                "type": "elision",
                "articles": [
                    "c",
                    "l",
                    "all",
                    "dall",
                    "dell",
                    "nell",
                    "sull",
                    "coll",
                    "pell",
                    "gl",
                    "agl",
                    "dagl",
                    "degl",
                    "negl",
                    "sugl",
                    "un",
                    "m",
                    "t",
                    "s",
                    "v",
                    "d",
                ],
                "articles_case": "true",
            },
            "lowercase",
            {"type": "stop", "stopwords": "_italian_"},
            {"type": "stemmer", "language": "light_italian"},
        ]
    },
    "ja": {
        "filter": [
            "cjk_width",
            "lowercase",
            "cjk_bigram",
            {"type": "stop", "stopwords": "_cjk_"},
        ]
    },
    "ko": {
        "filter": [
            "cjk_width",
            "lowercase",
            "cjk_bigram",
            {"type": "stop", "stopwords": "_cjk_"},
        ]
    },
    "lt": {
        "filter": [
            "lowercase",
            {"type": "stop", "stopwords": "_lithuanian_"},
            {"type": "stemmer", "language": "lithuanian"},
        ]
    },
    "nl": {
        "filter": [
            "lowercase",
            {"type": "stop", "stopwords": "_dutch_"},
            {
                "type": "stemmer_override",
                "rules": ["fiets=>fiets", "bromfiets=>bromfiets", "ei=>eier", "kind=>kinder"],
            },
            {"type": "stemmer", "language": "dutch"},
        ]
    },
    "no": {
        "filter": [
            "lowercase",
            {"type": "stop", "stopwords": "_norwegian_"},
            {"type": "stemmer", "language": "norwegian"},
        ]
    },
    "pl": {
        "plugin": True,
        "filter": [
            "lowercase",
            "polish_stop",
            "polish_stem",
        ],
    },
    "pt-BR": {
        "filter": [
            "lowercase",
            {"type": "stop", "stopwords": "_brazilian_"},
            {"type": "stemmer", "language": "brazilian"},
        ]
    },
    "pt-PT": {
        "filter": [
            "lowercase",
            {"type": "stop", "stopwords": "_portuguese_"},
            {"type": "stemmer", "language": "light_portuguese"},
        ]
    },
    "ro": {
        "filter": [
            "lowercase",
            {"type": "stop", "stopwords": "_romanian_"},
            {"type": "stemmer", "language": "romanian"},
        ]
    },
    "ru": {
        "filter": [
            "lowercase",
            {"type": "stop", "stopwords": "_russian_"},
            {"type": "stemmer", "language": "russian"},
        ]
    },
    "sv": {
        "filter": [
            "lowercase",
            {"type": "stop", "stopwords": "_swedish_"},
            {"type": "stemmer", "language": "swedish"},
        ]
    },
    "th": {
        "tokenizer": "thai",
        "filter": [
            "lowercase",
            "decimal_digit",
            {"type": "stop", "stopwords": "_thai_"},
        ],
    },
    "tr": {
        "filter": [
            "apostrophe",
            {"type": "lowercase", "language": "turkish"},
            {"type": "stop", "stopwords": "_turkish_"},
            {"type": "stemmer", "language": "turkish"},
        ]
    },
    "zh-CN": {
        "filter": [
            "cjk_width",
            "lowercase",
            "cjk_bigram",
            {"type": "stop", "stopwords": "_cjk_"},
        ]
    },
    "zh-TW": {
        "filter": [
            "cjk_width",
            "lowercase",
            "cjk_bigram",
            {"type": "stop", "stopwords": "_cjk_"},
        ]
    },
}

DEFAULT_ES7_CONNECTION = "es7_default"

# default refresh_interval for all indices
DEFAULT_ES7_REFRESH_INTERVAL = "60s"
