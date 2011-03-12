from django.utils.datastructures import SortedDict

from tower import ugettext_lazy as _lazy


products = SortedDict([
    ('desktop', {
        'name': _lazy(u'Firefox for Desktops or Laptops'),
        'subtitle': _lazy(u'Windows, Mac, or Linux'),
        'extra_fields': ['troubleshooting', 'ff_version', 'os', 'plugins'],
        'tags': ['desktop'],
        'class': 'for-fx3',  # If this sort of thing is needed more than once,
                             # refactor to use {for} machinery.
        'categories': SortedDict([
        ('d1', {
            'name': _lazy(u'Firefox is having problems with certain web sites'),
            'extra_fields': ['sites_affected'],
            'html': 'We have lots of helpful articles on <em>problems with web'
                    ' sites</em> and hundreds of questions in our database. '
                    'Try one of the following:',
            'articles': [
                {'title': 'Errors when loading web sites',
                 'url': '/en-US/kb/Error%20loading%20web%20sites'},
                {'title': 'Firefox cannot load websites but other programs can',
                 'url': '/en-US/kb/Firefox+cannot+load+websites+but+other+programs+can'},
                {'title': 'Web sites look wrong',
                 'url': '/en-US/kb/Websites+look+wrong'},
                {'title': 'Problems using Facebook in Firefox',
                 'url': '/en-US/kb/Problems+using+Facebook+in+Firefox'},
            ],
            'tags': ['websites'],
        }),
        ('d2', {
            'name': _lazy(u'Firefox is crashing or closing unexpectedly'),
            'extra_fields': ['crash_id'],
            'html': 'We have lots of helpful articles on <em>crashes</em> '
                    'and hundreds of questions in our database. Try one of '
                    'the following:',
            'articles': [
                {'title': 'Firefox crashes',
                 'url': '/en-US/kb/Firefox+Crashes'},
                {'title': 'Firefox crashes when you open it',
                 'url': '/en-US/kb/Firefox+crashes+when+you+open+it'},
                {'title': 'Firefox crashes when loading certain pages',
                 'url': '/en-US/kb/Firefox+crashes+when+loading+certain+pages'},
                {'title': 'Firefox crashes when you exit it',
                 'url': '/en-US/kb/Firefox+crashes+when+you+exit+it'},
                {'title': 'The Adobe Flash plugin has crashed',
                 'url': '/en-US/kb/The+Adobe+Flash+plugin+has+crashed'},
            ],
            'tags': ['crash'],
        }),
        ('d3', {
            'name': _lazy(u'I have a problem with my bookmarks, cookies, history or settings'),
            'html': 'We have lots of helpful articles on <em>bookmarks, '
                    'cookies, history or settings</em> and hundreds of '
                    'questions in our database. Try one of the following:',
            'articles': [
                {'title': 'Using Bookmarks',
                 'url': '/en-US/kb/Bookmarks'},
                {'title': 'Lost Bookmarks',
                 'url': '/en-US/kb/Lost%20Bookmarks'},
                {'title': 'Deleting Cookies',
                 'url': '/en-US/kb/Deleting+cookies'},
                {'title': 'Enabling and disabling cookies',
                 'url': '/en-US/kb/Enabling+and+disabling+cookies'},
            ],
            'tags': ['data'],
        }),
        ('d4', {
            'name': _lazy(u'I have a question about using a Firefox feature'),
            'html': 'We have lots of helpful articles to get you started <em>'
                    'learning and using Firefox</em> and hundreds of questions'
                    ' in our database. Try one of the following:',
            'articles': [
                {'title': 'How to set the home page',
                 'url': '/en-US/kb/How+to+set+the+home+page'},
                {'title': 'Private Browsing',
                 'url': '/en-US/kb/Private+Browsing'},
                {'title': 'Bookmarks',
                 'url': '/en-US/kb/Bookmarks'},
                {'title': 'Tabbed browsing',
                 'url': '/en-US/kb/Tabbed+browsing'},
                {'title': 'Location bar autocomplete',
                 'url': '/en-US/kb/Location+bar+autocomplete'},
            ],
            'tags': ['learning'],
        }),
        ('d5', {
            'name': _lazy(u'I have a problem with an extension or plugin'),
            'extra_fields': ['addon'],
            'html': 'Most extensions or plugins are not written by Mozilla '
                    'and you will need to contact the people or company who '
                    'made the extension/plugin for support, if you need help '
                    'removing an extension or plugin, see <a '
                    'href="/en-US/kb/Uninstalling+add-ons">Uninstalling '
                    'add-ons</a>.',
            'tags': ['addon'],
        }),
        ('d6', {
            'name': _lazy(u'I have another kind of problem with Firefox'),
            'extra_fields': ['frequency', 'started'],
            'html': 'We have lots of helpful articles on <em>general Firefox '
                    'issues</em> and hundreds of questions in our database. '
                    'Try one of the following:',
            'articles': [
                {'title': 'The Adobe Flash plugin has crashed',
                 'url': '/en-US/kb/The+Adobe+Flash+plugin+has+crashed'},
                {'title': 'What is plugin-container',
                 'url': '/en-US/kb/What+is+plugin-container'},
                {'title': 'How do I edit options to add Adobe to the list of allowed sites',
                 'url': '/en-US/kb/How+do+I+edit+options+to+add+Adobe+to+the+list+of+allowed+sites'},
                {'title': 'Menu bar is mising',
                 'url': '/en-US/kb/Menu+bar+is+missing'},
            ],
            'tags': ['general'],
        }),
        ])
    }),
    ('beta', {
        'name': _lazy(u'Firefox for Desktops or Laptops'),
        'subtitle': _lazy(u'Windows, Mac, or Linux'),
        'extra_fields': ['troubleshooting', 'ff_version', 'os', 'plugins'],
        'tags': ['desktop'],
        'class': 'for-not-fx3',
        'categories': SortedDict([
        ('b2', {
            'name': _lazy(u'Firefox is having problems with certain web sites'),
            'extra_fields': ['sites_affected'],
            'html': 'We have lots of helpful articles on <em>problems with web'
                    ' sites</em> and hundreds of questions in our database. '
                    'Try one of the following:',
            'articles': [
                {'title': 'Errors when loading web sites',
                 'url': '/en-US/kb/Error%20loading%20web%20sites'},
                {'title': 'Firefox cannot load websites but other programs can',
                 'url': '/en-US/kb/Firefox+cannot+load+websites+but+other+programs+can'},
                {'title': 'Web sites look wrong',
                 'url': 'en-US/kb/Websites%20look%20wrong'},
                {'title': 'Problems using Facebook in Firefox',
                 'url': '/en-US/kb/Problems+using+Facebook+in+Firefox'},
            ],
            'tags': ['websites'],
        }),
        ('b3', {
            'name': _lazy(u'Firefox is crashing or closing unexpectedly'),
            'extra_fields': ['crash_id'],
            'html': 'We have lots of helpful articles on <em>crashes</em> '
                    'and hundreds of questions in our database. Try one of '
                    'the following:',
            'articles': [
                {'title': 'Firefox crashes',
                 'url': '/en-US/kb/Firefox+Crashes'},
                {'title': 'Firefox crashes when you open it',
                 'url': '/en-US/kb/Firefox+crashes+when+you+open+it'},
                {'title': 'Firefox crashes when loading certain pages',
                 'url': '/en-US/kb/Firefox+crashes+when+loading+certain+pages'},
                {'title': 'Firefox crashes when you exit it',
                 'url': '/en-US/kb/Firefox+crashes+when+you+exit+it'},
                {'title': 'The Adobe Flash plugin has crashed',
                 'url': '/en-US/kb/The+Adobe+Flash+plugin+has+crashed'},
            ],
            'tags': ['crash'],
        }),
        ('data', {
            'name': _lazy(u'I have a problem with my bookmarks, cookies, history or settings'),
            'html': 'We have lots of helpful articles on <em>bookmarks, '
                    'cookies, history or settings</em> and hundreds of '
                    'questions in our database. Try one of the following:',
            'articles': [
                {'title': 'Using Bookmarks',
                 'url': '/en-US/kb/Bookmarks'},
                {'title': 'Lost Bookmarks',
                 'url': '/en-US/kb/Lost%20Bookmarks'},
                {'title': 'What happened to the bookmarks bar',
                 'url': '/en-US/kb/what-happened-bookmarks-toolbar'},
                {'title': 'Deleting Cookies',
                 'url': '/en-US/kb/Deleting+cookies'},
                {'title': 'Enabling and disabling cookies',
                 'url': '/en-US/kb/Enabling+and+disabling+cookies'},
            ],
            'tags': ['data'],
        }),
        ('learning', {
            'name': _lazy(u'I have a question about using a Firefox feature'),
            'html': 'We have lots of helpful articles to get you started <em>'
                    'learning and using Firefox</em> and hundreds of questions'
                    ' in our database. Try one of the following:',
            'articles': [
                {'title': 'What is Firefox Sync?',
                 'url': '/en-US/kb/what-firefox-sync'},
                {'title': 'What are App Tabs?',
                 'url': '/en-US/kb/what-are-app-tabs'},
                {'title': 'What is Panorama (also known as Tab Groups)?',
                 'url': '/en-US/kb/what-panorama'},
                {'title': 'What is the Add-on Bar?',
                 'url': '/en-US/kb/what-add-bar'},
                {'title': 'How do I use Private Browsing?',
                 'url': '/en-US/kb/Private+Browsing'},
            ],
            'tags': ['learning'],
        }),
        ('b4', {
            'name': _lazy(u'I have a problem with an extension or plugin'),
            'extra_fields': ['addon'],
            'html': 'Most extensions or plugins are not written by Mozilla '
                    'and you will need to contact the people or company who '
                    'made the extension/plugin for support, if you need help '
                    'removing an extension or plugin, see <a '
                    'href="/en-US/kb/Uninstalling+add-ons">Uninstalling '
                    'add-ons</a>.',
            'tags': ['addon'],
        }),
        ('b5', {
            'name': _lazy(u'I have another kind of problem with Firefox'),
            'extra_fields': ['frequency', 'started'],
            'html': 'We have lots of helpful articles on <em>general Firefox '
                    'issues</em> and hundreds of questions in our database. '
                    'Try one of the following:',
            'articles': [
                {'title': 'What happened to the Status bar?',
                 'url': '/en-US/kb/what-happened-status-bar'},
                {'title': 'What is plugin-container',
                 'url': '/en-US/kb/What+is+plugin-container'},
                {'title': 'Menu bar is mising',
                 'url': '/en-US/kb/Menu+bar+is+missing'},
            ],
            'tags': ['general'],
        }),
        ('b6', {
            'name': _lazy(u'I have suggestions for future versions of Firefox'),
            'html': 'If you\'re using the latest version of Firefox 4, you can '
                    'leave us suggestions for features at our '
                    '<a href="http://input.mozilla.com/feedback/">'
                    'feedback page</a>.',
            'deadend': True,
        }),
        ])
    }),
    ('mobile', {
        'name': _lazy(u'Firefox for Mobile'),
        'subtitle': _lazy(u'Android or Maemo systems'),
        'extra_fields': ['ff_version', 'os', 'plugins'],
        'tags': ['mobile'],
        'categories': SortedDict([
            ('m1', {
                'name': _lazy(u'Firefox for mobile is having problems with certain web sites'),
                'extra_fields': ['sites_affected'],
                'tags': ['websites'],
            }),
            ('m2', {
                'name': _lazy(u"I'm having trouble learning to use Firefox for mobile"),
                'html': 'We have lots of helpful articles to get you started '
                        '<em>learning to use Firefox for mobile</em> and '
                        'hundreds of questions in our database. Try one of the'
                        ' following:',
                'articles': [
                    {'title': 'How to navigate Web pages',
                     'url': 'http://support.mozilla.com/en-US/kb/surf-web-with-mobile-firefox'},
                    {'title': 'How to open a new tab',
                     'url': 'http://support.mozilla.com/en-US/kb/open-new-tab'},
                    {'title': 'How to add a bookmark',
                     'url': 'http://support.mozilla.com/en-US/kb/how-do-i-add-bookmark'},
                    {'title': 'How to use the Location Bar',
                     'url': 'http://support.mozilla.com/en-US/kb/how-do-i-use-awesome-screen'},
                    {'title': 'How to zoom in and out',
                     'url': 'http://support.mozilla.com/en-US/kb/zoom-in-and-out'},
                    {'title': 'How to manage downloads',
                     'url': 'http://support.mozilla.com/en-US/kb/manage-downloads'},
                ],
                'tags': ['learning'],
            }),
            ('m3', {
                'name': _lazy(u'Firefox for mobile is crashing or closing unexpectedly'),
                'tags': ['crash'],
            }),
            ('m4', {
                'name': _lazy(u'I have a problem with an extension or plugin'),
                'extra_fields': ['addon'],
                'html': 'Most extensions or plugins are not written by Mozilla '
                        'and you will need to contact the people or company who '
                        'made the extension/plugin for support, if you need help '
                        'removing an extension or plugin, see <a '
                        'href="http://support.mozilla.com'
                        '/en-US/kb/remove-or-disable-add-ons">'
                        'How to remove or disable add-ons</a>.',
                'tags': ['addon'],
            }),
            ('m5', {
                'name': _lazy(u'I have another kind of problem with Firefox for mobile'),
                'extra_fields': ['frequency'],
                'html': 'We have lots of helpful articles on <em>general '
                        'issues with Firefox for mobile</em> and hundreds '
                        'of questions in our database. Try one of the '
                        'following:',
                'articles': [
                    {'title': 'Will Firefox work on my phone',
                     'url': 'http://support.mozilla.com/en-US/kb/will-firefox-work-my-phone'},
                    {'title': 'How to install Firefox on N900',
                     'url': 'http://support.mozilla.com/en-US/kb/install-firefox-mobile'},
                    {'title': 'How to find and install add-ons',
                     'url': 'http://support.mozilla.com/en-US/kb/find-and-install-add-ons'},
                    {'title': 'How do I sync Firefox between my desktop and mobile?',
                     'url': 'http://support.mozilla.com/en-US/kb/sync-firefox-between-desktop-and-mobile'},
                    {'title': 'How do I remove or disable Add-ons?',
                     'url': 'http://support.mozilla.com/en-US/kb/remove-or-disable-add-ons'},
                    {'title': 'How do I change preferences?',
                     'url': 'http://support.mozilla.com/en-US/kb/change-preferences'},
                ],
                'tags': ['general'],
            }),
            ('m6', {
                'name': _lazy(u'I have suggestions for how to improve Firefox for mobile'),
                'html': '<p>You can provide suggestions for '
                        '<strong>Firefox on Android or Maemo</strong> in the '
                        '<a href="http://firefoxformobile.uservoice.com/forums/70211-firefox-for-mobile-ideas">'
                        'Firefox for mobile feedback forum</a>.</p>',
                'deadend': True,
            }),
        ])
    }),
    ('home', {
        'name': _lazy(u'Firefox Home'),
        'subtitle':  _lazy(u'App for iPhone'),
        'tags': ['FxHome'],
        'categories': SortedDict([
            ('i1', {
                'name': _lazy(u"I'm having trouble setting up Firefox Home on my iPhone"),
                'html': 'We have lots of helpful articles on <em>setting up '
                        'Firefox Home</em> and hundreds of questions in our '
                        'database. Try the following:',
                'articles': [
                    {'title': 'How to set up Firefox Home on your iPhone',
                     'url': '/en-US/kb/How+to+set+up+Firefox+Home+on+your+iPhone'},
                ],
                'tags': ['iphone'],
            }),
            ('i2', {
                'name': _lazy(u"I'm having trouble setting up Firefox Sync on my Desktop Firefox"),
                'html': 'We have lots of helpful articles on <em>setting up '
                        'Firefox Sync</em> and hundreds of questions in our '
                        'database. Try the following:',
                'articles': [
                    {'title': 'How to sync Firefox settings between computers',
                     'url': '/en-US/kb/How+to+sync+Firefox+settings+between+computers'},
                ],
                'tags': ['desktop', 'sync'],
            }),
            ('i3', {
                'name': _lazy(u'Not all my data is syncing between Firefox '
                          'and Firefox Home or I have other problems '),
                'html': 'We have lots of helpful articles on <em>Firefox Home '
                        'issues</em> and hundreds of questions in our '
                        'database. Try one of the following:',
                'articles': [
                    {'title': 'Firefox Home does not work ',
                     'url': '/kb/Firefox+Home+does+not+work'},
                    {'title': 'Cannot log in to Firefox Home App ',
                     'url': '/kb/Cannot+log+in+to+Firefox+Home+App'},
                    {'title': 'Replace your Sync information',
                     'url': '/kb/Replace+your+Sync+information'},
                ],
                'tags': ['general'],
            }),
            ('i4', {
                'name': _lazy(u'I have suggestions for how to improve Firefox Home for iPhone'),
                'html': 'You can provide suggestions in our '
                        '<a href="http://firefoxformobile.uservoice.com/forums/67057-firefox-home-ideas">'
                        'Firefox Home feedback forum</a>.',
                'deadend': True,
            }),
        ])
    }),
    ('sync', {
        'name': _lazy(u'Firefox Sync'),
        'tags': ['sync'],
        'categories': SortedDict([
            ('s1', {
                'name': _lazy(u"I'm having trouble setting up Firefox Sync on my Nokia or Android device"),
                'html': 'We have lots of helpful articles on <em>setting up '
                        'Firefox Sync in Firefox for mobile</em> and hundreds '
                        'of questions in our database. Try the following:',
                'articles': [
                    {'title': 'How do I sync Firefox between my desktop and mobile?',
                     'url': 'http://support.mozilla.com/en-US/kb/sync-firefox-between-desktop-and-mobile'},
                ],
                'tags': ['mobile'],
            }),
            ('s2', {
                'name': _lazy(u"I'm having trouble setting up Firefox Home on my iPhone"),
                'html': 'We have lots of helpful articles on <em>setting up '
                        'Firefox Home</em> and hundreds of questions in our '
                        'database. Try one of the following:',
                'articles': [
                    {'title': 'How to set up Firefox Home on your iPhone',
                     'url': '/en-US/kb/How+to+set+up+Firefox+Home+on+your+iPhone'},
                ],
                'tags': ['iphone'],
            }),
            ('s3', {
                'name': _lazy(u"I'm having trouble setting up Firefox Sync on my Desktop Firefox"),
                'html': 'We have lots of helpful articles on <em>setting up '
                        'Firefox Sync</em> and hundreds of questions in our '
                        'database. Try one of the following:',
                'articles': [
                    {'title': 'How to sync Firefox settings between computers',
                     'url': '/en-US/kb/How+to+sync+Firefox+settings+between+computers'},
                ],
                'tags': ['desktop'],
            }),
            ('s4', {
                'name': _lazy(u'I have other problems syncing data between computers or devices'),
                'html': 'We have lots of helpful articles on <em>Firefox sync'
                        '</em> and hundreds of questions in our database. Try '
                        'one of the following:',
                'articles': [
                    {'title': 'Firefox Sync is not working',
                     'url': '/en-US/kb/Firefox+Sync+is+not+working'},
                    {'title': 'Firefox Home does not work ',
                     'url': '/kb/Firefox+Home+does+not+work'},
                    {'title': 'Cannot log in to Firefox Home App ',
                     'url': '/kb/Cannot+log+in+to+Firefox+Home+App'},
                    {'title': 'Replace your Sync information',
                     'url': '/kb/Replace+your+Sync+information'},
                ],
                'tags': ['general'],
            }),
            ('s5', {
                'name': _lazy(u'I have suggestions for how to improve Firefox Sync'),
                'html': 'You can provide suggestions in our '
                        '<a href="http://assets2.getsatisfaction.com/mozilla_labs/products/mozilla_labs_weave_sync">'
                        'Firefox Sync feedback forum</a>.',
                'deadend': True,
            }),
        ])
    }),
    ('other', {
        'name': _lazy(u"Thunderbird"),
        'subtitle':  _lazy(u"or other Mozilla product"),
        'html': 'Support for Thunderbird and other Mozilla products can be found at'
                ' <a href="http://www.mozilla.org/support">Mozilla Support</a>.',
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
