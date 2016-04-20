from django.utils.datastructures import SortedDict
from django.utils.translation import ugettext_lazy as _lazy

# The number of answers per page.
ANSWERS_PER_PAGE = 20

# The number of questions per page.
QUESTIONS_PER_PAGE = 20

# Highest ranking to show for a user
HIGHEST_RANKING = 100

# Special tag names:
ESCALATE_TAG_NAME = 'escalate'
NEEDS_INFO_TAG_NAME = 'needsinfo'
OFFTOPIC_TAG_NAME = 'offtopic'

# Escalation config
ESCALATE_EXCLUDE_PRODUCTS = ['thunderbird', 'webmaker', 'open-badges']

# How long until a question is automatically taken away from a user
TAKE_TIMEOUT = 600

# AAQ config:
products = SortedDict([
    ('desktop', {
        'name': _lazy(u'Firefox'),
        'subtitle': _lazy(u'Web browser for Windows, Mac and Linux'),
        'extra_fields': ['troubleshooting', 'ff_version', 'os', 'plugins'],
        'tags': ['desktop'],
        'product': 'firefox',
        'categories': SortedDict([
            # TODO: Just use the IA topics for this.
            # See bug 979397
            ('download-and-install', {
                'name': _lazy(u'Download, install and migration'),
                'topic': 'download-and-install',
                'tags': ['download-and-install'],
            }),
            ('privacy-and-security', {
                'name': _lazy(u'Privacy and security settings'),
                'topic': 'privacy-and-security',
                'tags': ['privacy-and-security'],
            }),
            ('customize', {
                'name': _lazy(u'Customize controls, options and add-ons'),
                'topic': 'customize',
                'tags': ['customize'],
            }),
            ('fix-problems', {
                'name': _lazy(u'Fix slowness, crashing, error messages and '
                              u'other problems'),
                'topic': 'fix-problems',
                'tags': ['fix-problems'],
            }),
            ('tips', {
                'name': _lazy(u'Tips and tricks'),
                'topic': 'tips',
                'tags': ['tips'],
            }),
            ('bookmarks', {
                'name': _lazy(u'Bookmarks'),
                'topic': 'bookmarks',
                'tags': ['bookmarks'],
            }),
            ('cookies', {
                'name': _lazy(u'Cookies'),
                'topic': 'cookies',
                'tags': ['cookies'],
            }),
            ('tabs', {
                'name': _lazy(u'Tabs'),
                'topic': 'tabs',
                'tags': ['tabs'],
            }),
            ('websites', {
                'name': _lazy(u'Websites'),
                'topic': 'websites',
                'tags': ['websites'],
            }),
            ('sync', {
                'name': _lazy(u'Firefox Sync'),
                'topic': 'sync',
                'tags': ['sync'],
            }),
            ('other', {
                'name': _lazy(u'Other'),
                'topic': 'other',
                'tags': ['other'],
            }),
        ])
    }),

    ('mobile', {
        'name': _lazy(u'Firefox for Android'),
        'subtitle': _lazy(u'Web browser for Android smartphones and tablets'),
        'extra_fields': ['ff_version', 'os', 'plugins'],
        'tags': ['mobile'],
        'product': 'mobile',
        'categories': SortedDict([
            # TODO: Just use the IA topics for this.
            # See bug 979397
            ('download-and-install', {
                'name': _lazy(u'Download, install and migration'),
                'topic': 'download-and-install',
                'tags': ['download-and-install'],
            }),
            ('privacy-and-security', {
                'name': _lazy(u'Privacy and security settings'),
                'topic': 'privacy-and-security',
                'tags': ['privacy-and-security'],
            }),
            ('customize', {
                'name': _lazy(u'Customize controls, options and add-ons'),
                'topic': 'customize',
                'tags': ['customize'],
            }),
            ('fix-problems', {
                'name': _lazy(u'Fix slowness, crashing, error messages and '
                              u'other problems'),
                'topic': 'fix-problems',
                'tags': ['fix-problems'],
            }),
            ('tips', {
                'name': _lazy(u'Tips and tricks'),
                'topic': 'tips',
                'tags': ['tips'],
            }),
            ('bookmarks', {
                'name': _lazy(u'Bookmarks'),
                'topic': 'bookmarks',
                'tags': ['bookmarks'],
            }),
            ('cookies', {
                'name': _lazy(u'Cookies'),
                'topic': 'cookies',
                'tags': ['cookies'],
            }),
            ('tabs', {
                'name': _lazy(u'Tabs'),
                'topic': 'tabs',
                'tags': ['tabs'],
            }),
            ('websites', {
                'name': _lazy(u'Websites'),
                'topic': 'websites',
                'tags': ['websites'],
            }),
            ('sync', {
                'name': _lazy(u'Firefox Sync'),
                'topic': 'sync',
                'tags': ['sync'],
            }),
            ('other', {
                'name': _lazy(u'Other'),
                'topic': 'other',
                'tags': ['other'],
            }),
        ])
    }),

    ('ios', {
        'name': _lazy(u'Firefox for iOS'),
        'subtitle': _lazy(u'Firefox for iPhone, iPad and iPod touch devices'),
        'extra_fields': ['ff_version', 'os', 'plugins'],
        'tags': ['ios'],
        'product': 'ios',
        'categories': SortedDict([
            ('install-and-update-firefox-ios', {
                'name': _lazy(u'Install and Update'),
                'topic': 'install-and-update-firefox-ios',
                'tags': ['install-and-update-firefox-ios']
            }),
            ('how-to-use-firefox-ios', {
                'name': _lazy(u'How to use Firefox for iOS'),
                'topic': 'how-to-use-firefox-ios',
                'tags': ['how-to-use-firefox-ios']
            }),
            ('firefox-ios-not-working-expected', {
                'name': _lazy(u'Firefox for iOS is not working as expected'),
                'topic': 'firefox-ios-not-working-expected',
                'tags': ['firefox-ios-not-working-expected']
            }),
        ])
    }),

    ('focus', {
        'name': _lazy(u'Focus by Firefox'),
        'subtitle': _lazy(u'Content blocker for Safari'),
        'extra_fields': [],
        'tags': ['focus-firefox'],
        'product': 'focus-firefox',
        'categories': SortedDict([
            ('get-started', {
                'name': _lazy(u'Get started'),
                'topic': 'get-started',
                'tags': []
            }),
        ])
    }),

    ('firefox-os', {
        'name': _lazy(u'Firefox OS'),
        'subtitle': _lazy(u'Mobile OS for smartphones'),
        'extra_fields': ['device', 'os'],
        'tags': [],
        'product': 'firefox-os',
        'categories': SortedDict([
            # TODO: Just use the IA topics for this.
            # See bug 979397
            ('download-and-install', {
                'name': _lazy(u'Download and install apps'),
                'topic': 'marketplace',
                'tags': ['marketplace'],
            }),
            ('customize', {
                'name': _lazy(u'Customize controls, options, settings and '
                              u'preferences'),
                'topic': 'settings',
                'tags': ['settings'],
            }),
            ('fix-problems', {
                'name': _lazy(u'Fix slowness, crashing, error messages and '
                              u'other problems'),
                'topic': 'fix-problems',
                'tags': ['fix-problems'],
            }),
        ])
    }),

    ('webmaker', {
        'name': _lazy(u'Webmaker'),
        'subtitle': _lazy(u'Tools for creating and teaching the web'),
        'extra_fields': [],
        'tags': [],
        'product': 'webmaker',
        'categories': SortedDict([
            # TODO: Just use the IA topics for this.
            # See bug 979397
            ('popcorn-maker', {
                'name': _lazy(u'Using Popcorn Maker'),
                'topic': 'popcorn-maker',
                'tags': ['popcorn-maker'],
            }),
            ('thimble', {
                'name': _lazy(u'Using Thimble'),
                'topic': 'thimble',
                'tags': ['thimble'],
            }),
            ('x-ray-goggles', {
                'name': _lazy(u'Using X-Ray Goggles'),
                'topic': 'x-ray-goggles',
                'tags': ['x-ray-goggles'],
            }),
            ('get-the-most-from-webmaker', {
                'name': _lazy(u'Using a feature on webmaker.org'),
                'topic': 'get-the-most-from-webmaker',
                'tags': ['get-the-most-from-webmaker'],
            }),
            ('events-and-help-for-mentors', {
                'name': _lazy(u'Contributing to Webmaker'),
                'topic': 'events-and-help-for-mentors',
                'tags': ['events-and-help-for-mentors'],
            }),
        ])
    }),

    ('thunderbird', {
        'name': _lazy(u'Thunderbird'),
        'subtitle': _lazy(u'Email software for Windows, Mac and Linux'),
        'extra_fields': [],
        'tags': [],
        'product': 'thunderbird',
        'categories': SortedDict([
            # TODO: Just use the IA topics for this.
            # See bug 979397
            ('download-and-install', {
                'name': _lazy(u'Download, install and migration'),
                'topic': 'download-install-and-migration',
                'tags': ['download-and-install'],
            }),
            ('privacy-and-security', {
                'name': _lazy(u'Privacy and security settings'),
                'topic': 'privacy-and-security-settings',
                'tags': ['privacy-and-security'],
            }),
            ('customize', {
                'name': _lazy(u'Customize controls, options and add-ons'),
                'topic': 'customize-controls-options-and-add-ons',
                'tags': ['customize'],
            }),
            ('fix-problems', {
                'name': _lazy(u'Fix slowness, crashing, error messages and '
                              u'other problems'),
                'topic': 'fix-slowness-crashing-error-messages-and-other-'
                         'problems',
                'tags': ['fix-problems'],
            }),
            ('calendar', {
                'name': _lazy(u'Calendar'),
                'topic': 'calendar',
                'tags': ['calendar'],
            }),
            ('other', {
                'name': _lazy(u'Other'),
                'topic': 'other',
                'tags': ['other'],
            }),
        ])
    }),

    ('other', {
        'name': _lazy(u'Other Mozilla products'),
        'subtitle': '',
        'html': _lazy(u'This site only provides support for some of our products. '
                      u'For other support, please find your product below.'
                      u'<ul class="product-support">'
                      u'<li><a href="http://www.seamonkey-project.org/doc/">'
                      u'SeaMonkey support</a></li>'
                      u'<li><a href="http://caminobrowser.org/help/">'
                      u'Camino support</a></li>'
                      u'<li><a '
                      u'href="http://www.mozilla.org/projects/calendar/faq.html">'
                      u'Lightning and Sunbird support</a></li>'
                      u'</ul>'),
        'categories': SortedDict([]),
        'deadend': True,
    }),
])


def add_backtrack_keys(products):
    """Insert 'key' keys so we can go from product or category back to key."""
    for p_k, p_v in products.iteritems():
        p_v['key'] = p_k
        for c_k, c_v in p_v['categories'].iteritems():
            c_v['key'] = c_k


add_backtrack_keys(products)
