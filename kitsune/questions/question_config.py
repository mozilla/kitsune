from django.utils.datastructures import SortedDict

from tower import ugettext_lazy as _lazy


products = SortedDict([
    ('desktop', {
        'name': _lazy(u'Firefox for Desktop'),
        'subtitle': _lazy(u'Windows, Mac, or Linux'),
        'extra_fields': ['troubleshooting', 'ff_version', 'os', 'plugins'],
        'tags': ['desktop'],
        'products': ['firefox'],
        'categories': SortedDict([
            # TODO: Just use the IA topics for this.
            ('get-started', {
                'name': _lazy(u'Learn the Basics: get started'),
                'topic': 'get-started',
                'tags': ['get-started'],
            }),
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
                'name': _lazy(u'Fix slowness, crashing, error messages and other problems'),
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
        ])
    }),
    ('mobile', {
        'name': _lazy(u'Firefox for Mobile'),
        'subtitle': _lazy(u'Android'),
        'extra_fields': ['ff_version', 'os', 'plugins'],
        'tags': ['mobile'],
        'products': ['mobile'],
        'categories': SortedDict([
            # TODO: Just use the IA topics for this.
            ('get-started', {
                'name': _lazy(u'Learn the Basics: get started'),
                'topic': 'get-started',
                'tags': ['get-started'],
            }),
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
                'name': _lazy(u'Fix slowness, crashing, error messages and other problems'),
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
        ])
    }),
    ('firefox-os', {
        'name': _lazy(u'Firefox OS'),
        'subtitle': '',
        'extra_fields': [],
        'tags': [],
        'products': ['firefox-os'],
        'categories': SortedDict([
            # TODO: Just use the IA topics for this.
            ('download-and-install', {
                'name': _lazy(u'Download and install apps'),
                'topic': 'download-and-install',
                'tags': ['download-and-install'],
            }),
            ('customize', {
                'name': _lazy(u'Customize controls, options, settings and preferences'),
                'topic': 'customize',
                'tags': ['customize'],
            }),
            ('fix-problems', {
                'name': _lazy(u'Fix slowness, crashing, error messages and other problems'),
                'topic': 'fix-problems',
                'tags': ['fix-problems'],
            }),
        ])
    }),
    ('other', {
        'name': _lazy(u'Thunderbird'),
        'subtitle':  _lazy(u'or other Mozilla products'),
        'html': 'This site is only for Firefox support. Please find your '
                'product below.'
                '<ul class="product-support">'
                '<li><a href="http://support.mozillamessaging.com/">'
                'Thunderbird support</a></li>'
                '<li><a href="http://www.seamonkey-project.org/doc/">'
                'SeaMonkey support</a></li>'
                '<li><a href="http://caminobrowser.org/help/">'
                'Camino support</a></li>'
                '<li><a '
                'href="http://www.mozilla.org/projects/calendar/faq.html">'
                'Lightning and Sunbird support</a></li>'
                '</ul>',
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
