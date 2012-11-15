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
    ('sync', {
        'name': _lazy(u'Firefox Sync'),
        'tags': ['sync'],
        'categories': SortedDict([
            ('s1', {
                'name': _lazy(u"Setting up Firefox Sync on my Android device"),
                'html': 'We have lots of helpful articles on <em>setting up '
                        'Firefox Sync in Firefox for mobile</em> and hundreds '
                        'of questions in our database. Try the following:',
                'articles': [
                    {'document_title': 'How do I sync Firefox between my desktop and '
                              'mobile?',
                     'url': '/kb/sync-firefox-between-desktop-and-mobile'},
                    {'document_title': 'How do I add a device to Firefox Sync?',
                     'url': '/kb/add-a-device-to-firefox-sync'},
                ],
                'tags': ['mobile'],
            }),
            ('s2', {
                'name': _lazy(u"Setting up Firefox Home on my iPhone"),
                'html': 'We have lots of helpful articles on <em>setting up '
                        'Firefox Home</em> and hundreds of questions in our '
                        'database. Try one of the following:',
                'articles': [
                    {'document_title': 'How to set up Firefox Home on your iPhone',
                     'url': '/kb/How+to+set+up+Firefox+Home+on+your+iPhone'},
                ],
                'tags': ['iphone'],
            }),
            ('s3', {
                'name': _lazy(u'Setting up Firefox Sync on my Desktop '
                              u'Firefox'),
                'html': 'We have lots of helpful articles on <em>setting up '
                        'Firefox Sync</em> and hundreds of questions in our '
                        'database. Try one of the following:',
                'articles': [
                    {'document_title': 'How to sync Firefox settings between computers',
                     'url': '/kb/How%20to%20sync%20Firefox%20settings%20'
                            'between%20computers'},
                    {'document_title': 'How do I set up Firefox Sync?',
                     'url': '/kb/how-do-i-set-up-firefox-sync'},
                ],
                'tags': ['desktop'],
            }),
            ('s4', {
                'name': _lazy(u'Other problems syncing data between computers '
                              u'or devices'),
                'html': 'We have lots of helpful articles on <em>Firefox sync'
                        '</em> and hundreds of questions in our database. Try '
                        'one of the following:',
                'articles': [
                    {'document_title': 'Firefox Sync is not working',
                     'url': '/kb/Firefox+Sync+is+not+working'},
                    {'document_title': 'Firefox Home does not work ',
                     'url': '/kb/Firefox+Home+does+not+work'},
                    {'document_title': 'Cannot log in to Firefox Home App ',
                     'url': '/kb/Cannot+log+in+to+Firefox+Home+App'},
                    {'document_title': 'Replace your Sync information',
                     'url': '/kb/Replace+your+Sync+information'},
                ],
                'tags': ['other'],
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
