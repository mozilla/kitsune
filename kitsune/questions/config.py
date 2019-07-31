from collections import OrderedDict

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
products = OrderedDict([
    ('desktop', {
        'name': _lazy(u'Firefox'),
        'subtitle': _lazy(u'Web browser for Windows, Mac and Linux'),
        'extra_fields': ['troubleshooting', 'ff_version', 'os', 'plugins'],
        'tags': ['desktop'],
        'product': 'firefox',
        'categories': OrderedDict([
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
        'categories': OrderedDict([
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
        'categories': OrderedDict([
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
        'name': _lazy(u'Firefox Focus'),
        'subtitle': _lazy(u'Automatic privacy browser and content blocker'),
        'extra_fields': [],
        'tags': ['focus-firefox'],
        'product': 'focus-firefox',
        'categories': OrderedDict([
            ('Focus-ios', {
                'name': _lazy(u'Firefox Focus for iOS'),
                'topic': 'Focus-ios',
                'tags': ['Focus-ios']
            }),
            ('firefox-focus-android', {
                'name': _lazy(u'Firefox Focus for Android'),
                'topic': 'firefox-focus-android',
                'tags': ['firefox-focus-android']
            }),
        ])
    }),

    ('firefox-amazon-devices', {
        'name': _lazy(u'Firefox for Amazon Devices'),
        'subtitle': _lazy(u'Browser for Amazon devices'),
        'extra_fields': [],
        'tags': ['firefox-amazon'],
        'product': 'firefox-amazon-devices',
        'categories': OrderedDict([
            ('firefox-fire-tv', {
                'name': _lazy(u'Firefox for Fire TV'),
                'topic': 'firefox-fire-tv',
                'tags': ['firefox-fire-tv']
            }),
            ('firefox-echo-show', {
                'name': _lazy(u'Firefox for Echo Show'),
                'topic': 'firefox-echo-show',
                'tags': ['firefox-echo-show']
            }),
        ])
    }),

    ('thunderbird', {
        'name': _lazy(u'Thunderbird'),
        'subtitle': _lazy(u'Email software for Windows, Mac and Linux'),
        'extra_fields': [],
        'tags': [],
        'product': 'thunderbird',
        'categories': OrderedDict([
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

    ('firefox-lite', {
        'name': _lazy(u'Firefox Lite'),
        'subtitle': _lazy(u'Mobile browser for Indonesia'),
        'extra_fields': [],
        'tags': ['firefox-lite'],
        'product': 'firefox-lite',
        'categories': OrderedDict([
            ('get-started', {
                'name': _lazy(u'Get started'),
                'topic': 'get-started',
                'tags': ['get-started']
            }),
            ('fix-problems', {
                'name': _lazy(u'Fix problems'),
                'topic': 'fix-problems',
                'tags': ['fix-problems']
            }),
        ])
    }),

    ('firefox-enterprise', {
        'name': _lazy(u'Firefox for Enterprise'),
        'subtitle': _lazy(u'Enterprise version of Firefox'),
        'extra_fields': [],
        'tags': [],
        'product': 'firefox-enterprise',
        'categories': OrderedDict([
            ('deploy-firefox-for-enterprise', {
                'name': _lazy(u'Deploy'),
                'topic': 'deploy-firefox-for-enterprise',
                'tags': ['deployment'],
            }),
            ('policies-customization-enterprise', {
                'name': _lazy(u'Manage updates, policies & customization'),
                'topic': 'policies-customization-enterprise',
                'tags': ['customization'],
            }),
            ('manage-add-ons-enterprise', {
                'name': _lazy(u'Manage add-ons'),
                'topic': 'manage-add-ons-enterprise',
                'tags': ['customization'],
            }),
            ('manage-certificates-firefox-enterprise', {
                'name': _lazy(u'Manage certificates'),
                'topic': 'manage-certificates-firefox-enterprise',
                'tags': ['customization'],
            }),
        ])
    }),

    ('firefox-reality', {
        'name': _lazy(u'Firefox Reality'),
        'subtitle': _lazy(u'Firefox for Virtual Reality'),
        'extra_fields': [],
        'tags': [],
        'product': 'firefox-reality',
        'categories': OrderedDict([
            ('get-started', {
                'name': _lazy(u'Get started with Firefox Reality'),
                'topic': 'get-started',
                'tags': ['get-started'],
            }),
            ('troubleshooting-reality', {
                'name': _lazy(u'Troubleshooting Firefox Reality'),
                'topic': 'troubleshooting-reality',
                'tags': ['troubleshooting'],
            }),
        ])
    }),

    ('firefox-preview', {
        'name': _lazy(u'Firefox Preview'),
        'subtitle': _lazy(u'Firefox for Android'),
        'extra_fields': [],
        'tags': [],
        'product': 'firefox-preview',
        'categories': OrderedDict([
            ('install-and-update-firefox-preview', {
                'name': _lazy(u'Install and Update'),
                'topic': 'install-and-update',
                'tags': ['download-and-install'],
            }),
            ('how-to-use-firefox-preview', {
                'name': _lazy(u'How do I use Firefox Preview'),
                'topic': 'how-do-i-use-firefox-preview',
                'tags': ['tips'],
            }),
            ('browsing-firefox-preview', {
                'name': _lazy(u'Browsing'),
                'topic': 'browsing-preview',
                'tags': ['tips'],
            }),
            ('library-firefox-preview', {
                'name': _lazy(u'Library'),
                'topic': 'library',
                'tags': ['library'],
            }),
            ('sync-firefox-preview', {
                'name': _lazy(u'Sync'),
                'topic': 'sync-preview',
                'tags': ['sync'],
            }),
            ('privacy-and-security-firefox-preview', {
                'name': _lazy(u'Privacy and Security'),
                'topic': 'privacy-and-security',
                'tags': ['privacy-and-security'],
            }),
            ('fix-problems-with-firefox-preview', {
                'name': _lazy(u'Fix problems with Firefox Preview'),
                'topic': 'fix-problems-firefox-preview',
                'tags': ['fix-problems'],
            }),
            ('settings-and-preferences-firefox-preview', {
                'name': _lazy(u'Settings and Preferences'),
                'topic': 'settings-prefs-preview',
                'tags': ['customize'],
            }),
            ('advanced-settings-firefox-preview', {
                'name': _lazy(u'Advanced Settings'),
                'topic': 'advanced-settings-preview',
                'tags': ['customize'],
            }),
        ])
    }),

    ('firefox-lockwise', {
        'name': _lazy(u'Firefox Lockwise'),
        'subtitle': _lazy(u'Firefox Lockwise'),
        'extra_fields': [],
        'tags': [],
        'product': 'firefox-lockwise',
        'categories': OrderedDict([
            ('install-and-set-up', {
                'name': _lazy(u'Install and set up'),
                'topic': 'install-lockwise',
                'tags': ['install-and-set-up'],
            }),
            ('manage-settings-and-logins', {
                'name': _lazy(u'Manage settings and logins'),
                'topic': 'lockwise-settings',
                'tags': ['settings-and-logins'],
            }),
            ('fix-problems-with-firefox-lockwise', {
                'name': _lazy(u'Fix problems with Firefox Lockwise'),
                'topic': 'fix-problems-lockwise',
                'tags': ['fix-problems'],
            }),
        ])
    }),

    ('other', {
        'name': _lazy(u'Other Mozilla products'),
        'subtitle': '',
        'product': '',
        'html': _lazy(u'This site only provides support for some of our products. '
                      u'For other support, please find your product below.'
                      u'<ul class="product-support">'
                      u'<li><a href="http://www.seamonkey-project.org/doc/">'
                      u'SeaMonkey support</a></li>'
                      u'<li><a '
                      u'href="/questions/new/thunderbird">'
                      u'Lightning support</a></li>'
                      u'</ul>'),
        'categories': OrderedDict([]),
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
