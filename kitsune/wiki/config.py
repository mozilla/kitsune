from tower import ugettext_lazy as _lazy

# Wiki configuration.

# Defines products supported, categories, edit significances and
# redirect related constants.

# Disruptiveness of edits to translated versions. Numerical magnitude indicate
# the relative severity.
TYPO_SIGNIFICANCE = 10
MEDIUM_SIGNIFICANCE = 20
MAJOR_SIGNIFICANCE = 30

SIGNIFICANCES = [
    (TYPO_SIGNIFICANCE,
     _lazy(u"Minor details that don't affect the instructions")),
    (MEDIUM_SIGNIFICANCE,
     _lazy(u"Content changes that don't require immediate translation")),
    (MAJOR_SIGNIFICANCE,
     _lazy(u'Major content changes that will make older translations '
           'inaccurate')),
]

SIGNIFICANCES_HELP = {
    TYPO_SIGNIFICANCE: _lazy(
        u'These minor changes are not important for localizers and '
        u'they will not be notified.'),
    MEDIUM_SIGNIFICANCE: _lazy(
        u'This will notify localizers and translations will be marked as '
        u'"needing updates" on dashboards. Most changes&mdash;updating an '
        u'image, fixing {for} markup, adding or removing non-critical '
        u'sections&mdash;should use this.'),
    MAJOR_SIGNIFICANCE: _lazy(
        u'This will notify localizers and translations will be marked '
        u'"out of date" on dashboards. Translations will show a warning '
        u'to users that they are out of date and that the English '
        u'version is the most accurate. Use this when the old '
        u'instructions are completely unusable.'),
}

TROUBLESHOOTING_CATEGORY = 10
HOW_TO_CATEGORY = 20
HOW_TO_CONTRIBUTE_CATEGORY = 30
ADMINISTRATION_CATEGORY = 40
NAVIGATION_CATEGORY = 50
TEMPLATES_CATEGORY = 60
CANNED_RESPONSES_CATEGORY = 70

CATEGORIES = (
    (TROUBLESHOOTING_CATEGORY, _lazy(u'Troubleshooting')),
    (HOW_TO_CATEGORY, _lazy(u'How to')),
    (HOW_TO_CONTRIBUTE_CATEGORY, _lazy(u'How to contribute')),
    (ADMINISTRATION_CATEGORY, _lazy(u'Administration')),
    (NAVIGATION_CATEGORY, _lazy(u'Navigation')),
    (TEMPLATES_CATEGORY, _lazy(u'Templates')),
    (CANNED_RESPONSES_CATEGORY, _lazy(u'Canned Responses')),
)

REDIRECT_HTML = '<p>REDIRECT <a '  # how a redirect looks as rendered HTML
REDIRECT_CONTENT = 'REDIRECT [[%s]]'
REDIRECT_TITLE = _lazy(u'%(old)s Redirect %(number)i')
REDIRECT_SLUG = _lazy(u'%(old)s-redirect-%(number)i')
