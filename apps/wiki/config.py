from collections import namedtuple
from itertools import chain

from tower import ugettext_lazy as _lazy

# Wiki configuration.
# Defines Firefox versions, operating systems, products supported,
# categories, edit significances and redirect related constants.


# FF versions used to filter article searches, power {for} tags, etc.:
#
# Iterables of (ID, name, abbreviation for {for} tags, max version this version
# group encompasses, whether-this-version-should-show-in-the-menu, and whether-
# this-version-is-the-default-on-this-platform), grouped into optgroups by
# platform. To add the ability to sniff a new version of an existing browser
# (assuming it doesn't change the user agent string too radically), you should
# need only to add a line here; no JS required. Just be wary of inexact
# floating point comparisons when setting max_version, which should be read as
# "From the next smaller max_version up to but not including version x.y".
#
# When a wiki page is being viewed in a desktop browser, the {for} sections for
# the default mobile browser still show. The reverse is true when a page is
# being viewed in a mobile browser.
VersionMetadata = namedtuple('VersionMetadata',
                             'id, name, long, slug, max_version, show_in_ui, '
                             'is_default')
GROUPED_FIREFOX_VERSIONS = (
    ((_lazy(u'Desktop:'), 'desktop'), (
        VersionMetadata(23, _lazy(u'Firefox 14'),
                        _lazy(u'Firefox 14'), 'fx14', 14.9999, True, False),
        VersionMetadata(21, _lazy(u'Firefox 13'),
                        _lazy(u'Firefox 13'), 'fx13', 13.9999, True, True),
        VersionMetadata(19, _lazy(u'Firefox 12'),
                        _lazy(u'Firefox 12'), 'fx12', 12.9999, True, False),
        VersionMetadata(17, _lazy(u'Firefox 11'),
                        _lazy(u'Firefox 11'), 'fx11', 11.9999, True, False),
        VersionMetadata(15, _lazy(u'Firefox ESR'),
                        _lazy(u'Firefox ESR'), 'fx10', 10.9999, True, False),
        VersionMetadata(13, _lazy(u'Firefox 9'),
                        _lazy(u'Firefox 9'), 'fx9', 9.9999, False, False),
        VersionMetadata(11, _lazy(u'Firefox 8'),
                        _lazy(u'Firefox 8'), 'fx8', 8.9999, False, False),
        VersionMetadata(9, _lazy(u'Firefox 7'),
                        _lazy(u'Firefox 7'), 'fx7', 7.9999, False, False),
        VersionMetadata(6, _lazy(u'Firefox 6'),
                        _lazy(u'Firefox 6'), 'fx6', 6.9999, False, False),
        VersionMetadata(5, _lazy(u'Firefox 5'),
                        _lazy(u'Firefox 5'), 'fx5', 5.9999, False, False),
        VersionMetadata(1, _lazy(u'Firefox 4'),
                        _lazy(u'Firefox 4'), 'fx4', 4.9999, False, False),
        VersionMetadata(2, _lazy(u'Firefox 3.5-3.6'),
                        _lazy(u'Firefox 3.5-3.6'), 'fx35', 3.9999, False,
                        False),
        VersionMetadata(3, _lazy(u'Firefox 3.0'),
                        _lazy(u'Firefox 3.0'), 'fx3', 3.4999, False, False))),
    ((_lazy(u'Mobile:'), 'mobile'), (
        VersionMetadata(22, _lazy(u'Firefox 14'),
                        _lazy(u'Firefox 14 for Mobile'), 'm14', 14.9999,
                        True, False),
        # Firefox 13 for Mobile was skipped.
        VersionMetadata(20, _lazy(u'Firefox 12'),
                        _lazy(u'Firefox 12 for Mobile'), 'm12', 12.9999,
                        False, False),  # 11 and 12 for mobile were skipped.
        VersionMetadata(18, _lazy(u'Firefox 11'),
                        _lazy(u'Firefox 11 for Mobile'), 'm11', 11.9999,
                        False, False),  # 11 and 12 for mobile were skipped.
        VersionMetadata(16, _lazy(u'Firefox 10'),
                        _lazy(u'Firefox 10 for Mobile'), 'm10', 10.9999,
                        True, True),
        VersionMetadata(14, _lazy(u'Firefox 9'),
                        _lazy(u'Firefox 9 for Mobile'), 'm9', 9.9999,
                        False, False),
        VersionMetadata(12, _lazy(u'Firefox 8'),
                        _lazy(u'Firefox 8 for Mobile'), 'm8', 8.9999,
                        False, False),
        VersionMetadata(10, _lazy(u'Firefox 7'),
                        _lazy(u'Firefox 7 for Mobile'), 'm7', 7.9999,
                        False, False),
        VersionMetadata(8, _lazy(u'Firefox 6'),
                        _lazy(u'Firefox 6 for Mobile'), 'm6', 6.9999,
                        False, False),
        VersionMetadata(7, _lazy(u'Firefox 5'),
                        _lazy(u'Firefox 5 for Mobile'), 'm5', 5.9999,
                        False, False),
        VersionMetadata(4, _lazy(u'Firefox 4'),
                        _lazy(u'Firefox 4 for Mobile'), 'm4', 4.9999,
                        False, False),)))

# Flattened:
# TODO: Perhaps use optgroups everywhere instead.
FIREFOX_VERSIONS = tuple(chain(*[options for label, options in
                                 GROUPED_FIREFOX_VERSIONS]))

# OSes used to filter articles and declare {for} sections:
OsMetaData = namedtuple('OsMetaData', 'id, name, slug, show_in_ui, '
                        'is_default')
GROUPED_OPERATING_SYSTEMS = (
    ((_lazy(u'Desktop OS:'), 'desktop'), (
        OsMetaData(1, _lazy(u'Windows'), 'win', True, True),
        OsMetaData(2, _lazy(u'Mac OS X'), 'mac', True, False),
        OsMetaData(3, _lazy(u'Linux'), 'linux', True, False))),
    ((_lazy(u'Mobile OS:'), 'mobile'), (
        OsMetaData(5, _lazy(u'Android'), 'android', True, True),
        OsMetaData(4, _lazy(u'Maemo'), 'maemo', False, False))))

# Flattened
OPERATING_SYSTEMS = tuple(chain(*[options for label, options in
                                  GROUPED_OPERATING_SYSTEMS]))

# Products supported
Product = namedtuple('Product', 'slug, name')  # slug is used for tag/topic
PRODUCTS = (
    Product('desktop', _lazy(u'Desktop')),
    Product('mobile', _lazy(u'Mobile')),
    Product('sync', _lazy(u'Sync')),
    Product('FxHome', _lazy(u'Home')),
    Product('marketplace', _lazy(u'Marketplace')))
PRODUCT_TAGS = [p.slug for p in PRODUCTS]


# Disruptiveness of edits to translated versions. Numerical magnitude indicate
# the relative severity.
TYPO_SIGNIFICANCE = 10
MEDIUM_SIGNIFICANCE = 20
MAJOR_SIGNIFICANCE = 30

SIGNIFICANCES = [
    (TYPO_SIGNIFICANCE,
     _lazy(u'Minor details like punctuation and spelling errors')),
    (MEDIUM_SIGNIFICANCE,
     _lazy(u"Content changes that don't require immediate translation")),
    (MAJOR_SIGNIFICANCE,
     _lazy(u'Major content changes that will make older translations '
           'inaccurate')),
]

SIGNIFICANCES_HELP = {
    TYPO_SIGNIFICANCE:
        _lazy(u'These changes are inconsequential to localizers: they will '
              'not be notified of the change and it will not affect '
              'translations of the article.'),
    MEDIUM_SIGNIFICANCE:
        _lazy(u'This will notify localizers and translations will be marked '
              'as "needing updates" on dashboards. Most '
              'changes&mdash;updating an image, fixing {for} markup, adding '
              'or removing non-critical sections&mdash;should use this.'),
    MAJOR_SIGNIFICANCE:
        _lazy(u'This will notify localizers and translations will be marked '
              '"out of date" on dashboards. Translations will show a warning '
              'to users that they are out of date and that the English '
              'version is the most accurate. Use this when the old '
              'instructions are completely unusable.'),
}

CATEGORIES = (
    (10, _lazy(u'Troubleshooting')),
    (20, _lazy(u'How to')),
    (30, _lazy(u'How to contribute')),
    (40, _lazy(u'Administration')),
    (50, _lazy(u'Navigation')),
    (60, _lazy(u'Templates')),
)

REDIRECT_HTML = '<p>REDIRECT <a '  # how a redirect looks as rendered HTML
REDIRECT_CONTENT = 'REDIRECT [[%s]]'
REDIRECT_TITLE = _lazy(u'%(old)s Redirect %(number)i')
REDIRECT_SLUG = _lazy(u'%(old)s-redirect-%(number)i')
