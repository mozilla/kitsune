from django.utils.translation import ugettext_lazy as _lazy

TEMPLATE_TITLE_PREFIX = "Template:"
DOCUMENTS_PER_PAGE = 100

COLLAPSIBLE_DOCUMENTS = {
    "en-US": [
        "firefox-os-support-forum-contributors-training",
        "firefox-android-support-forum-contributors",
        "firefox-support-forum-contributors",
        "introduction-contributor-quality-training",
        "angry-user-training",
        "evaluating-solution-forum",
        "how-answer-escalated-questions",
        "navigate-support-forum-platform",
        "how-stop-firefox-making-automatic-connections",
    ],
    "cs": ["jak-firefoxu-zabranit-v-automatickem-navazovani-sp",],
    "de": ["Firefox-baut-unaufgeforderte-Verbindungen-auf",],
    "it": ["firefox-connessioni-non-richieste",],
    "pt-BR": ["como-fazer-o-firefox-parar-de-se-conectar-automati",],
}
FALLBACK_LOCALES = {
    "ca": ["es"],  # Bug 800880
    "eu": ["es"],  # Bug 800880
    "gl": ["es"],  # Bug 800880
    "wo": ["fr"],  # Bug 800880
    "fy-NL": ["nl"],  # Bug 800880
}

# Wiki configuration.

# Defines products supported, categories, edit significances and
# redirect related constants.

# Disruptiveness of edits to translated versions. Numerical magnitude indicate
# the relative severity.
TYPO_SIGNIFICANCE = 10
MEDIUM_SIGNIFICANCE = 20
MAJOR_SIGNIFICANCE = 30

SIGNIFICANCES = [
    (TYPO_SIGNIFICANCE, _lazy("Minor details that don't affect the instructions")),
    (MEDIUM_SIGNIFICANCE, _lazy("Content changes that don't require immediate translation"),),
    (
        MAJOR_SIGNIFICANCE,
        _lazy("Major content changes that will make older translations " "inaccurate"),
    ),
]

SIGNIFICANCES_HELP = {
    TYPO_SIGNIFICANCE: _lazy(
        "These minor changes are not important for localizers and " "they will not be notified."
    ),
    MEDIUM_SIGNIFICANCE: _lazy(
        "This will notify localizers and translations will be marked as "
        '"needing updates" on dashboards. Most changes&mdash;updating an '
        "image, fixing {for} markup, adding or removing non-critical "
        "sections&mdash;should use this."
    ),
    MAJOR_SIGNIFICANCE: _lazy(
        "This will notify localizers and translations will be marked "
        '"out of date" on dashboards. Translations will show a warning '
        "to users that they are out of date and that the English "
        "version is the most accurate. Use this when the old "
        "instructions are completely unusable."
    ),
}

TROUBLESHOOTING_CATEGORY = 10
HOW_TO_CATEGORY = 20
HOW_TO_CONTRIBUTE_CATEGORY = 30
ADMINISTRATION_CATEGORY = 40
NAVIGATION_CATEGORY = 50
TEMPLATES_CATEGORY = 60
CANNED_RESPONSES_CATEGORY = 70

CATEGORIES = (
    (TROUBLESHOOTING_CATEGORY, _lazy("Troubleshooting")),
    (HOW_TO_CATEGORY, _lazy("How to")),
    (HOW_TO_CONTRIBUTE_CATEGORY, _lazy("How to contribute")),
    (ADMINISTRATION_CATEGORY, _lazy("Administration")),
    (NAVIGATION_CATEGORY, _lazy("Navigation")),
    (TEMPLATES_CATEGORY, _lazy("Templates")),
    (CANNED_RESPONSES_CATEGORY, _lazy("Canned Responses")),
)

REDIRECT_HTML = "<p>REDIRECT <a "  # how a redirect looks as rendered HTML
REDIRECT_CONTENT = "REDIRECT [[%s]]"
REDIRECT_TITLE = _lazy("%(old)s Redirect %(number)i")
REDIRECT_SLUG = _lazy("%(old)s-redirect-%(number)i")

# Template for the cache key of the full article html.
DOC_HTML_CACHE_KEY = "doc_html:{locale}:{slug}"

SIMPLE_WIKI_LANDING_PAGE_SLUG = "frequently-asked-questions"
