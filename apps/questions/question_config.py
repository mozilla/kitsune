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
                 'url': '/kb/Error%20loading%20web%20sites'},
                {'title': 'Firefox cannot load websites but other programs can',
                 'url': '/kb/Firefox+cannot+load+websites+but+other+programs+can'},
                {'title': 'Web sites look wrong',
                 'url': '/kb/Websites+look+wrong'},
                {'title': 'Problems using Facebook in Firefox',
                 'url': '/kb/Problems+using+Facebook+in+Firefox'},
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
                 'url': '/kb/Firefox+Crashes'},
                {'title': 'Firefox crashes when you open it',
                 'url': '/kb/Firefox+crashes+when+you+open+it'},
                {'title': 'Firefox crashes when loading certain pages',
                 'url': '/kb/Firefox+crashes+when+loading+certain+pages'},
                {'title': 'Firefox crashes when you exit it',
                 'url': '/kb/Firefox+crashes+when+you+exit+it'},
                {'title': 'The Adobe Flash plugin has crashed',
                 'url': '/kb/The+Adobe+Flash+plugin+has+crashed'},
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
                 'url': '/kb/Bookmarks'},
                {'title': 'Lost Bookmarks',
                 'url': '/kb/Lost%20Bookmarks'},
                {'title': 'Deleting Cookies',
                 'url': '/kb/Deleting+cookies'},
                {'title': 'Enabling and disabling cookies',
                 'url': '/kb/Enabling+and+disabling+cookies'},
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
                 'url': '/kb/How+to+set+the+home+page'},
                {'title': 'Private Browsing',
                 'url': '/kb/Private+Browsing'},
                {'title': 'Bookmarks',
                 'url': '/kb/Bookmarks'},
                {'title': 'Tabbed browsing',
                 'url': '/kb/Tabbed+browsing'},
                {'title': 'Location bar autocomplete',
                 'url': '/kb/Location+bar+autocomplete'},
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
                    'href="/kb/Uninstalling+add-ons">Uninstalling '
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
                 'url': '/kb/The+Adobe+Flash+plugin+has+crashed'},
                {'title': 'What is plugin-container',
                 'url': '/kb/What+is+plugin-container'},
                {'title': 'How do I edit options to add Adobe to the list of allowed sites',
                 'url': '/kb/How+do+I+edit+options+to+add+Adobe+to+the+list+of+allowed+sites'},
                {'title': 'Menu bar is mising',
                 'url': '/kb/Menu+bar+is+missing'},
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
                 'url': '/kb/Error%20loading%20web%20sites'},
                {'title': 'Firefox cannot load websites but other programs can',
                 'url': '/kb/Firefox+cannot+load+websites+but+other+programs+can'},
                {'title': 'Web sites look wrong',
                 'url': '/kb/Websites%20look%20wrong'},
                {'title': 'Problems using Facebook in Firefox',
                 'url': '/kb/Problems+using+Facebook+in+Firefox'},
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
                 'url': '/kb/Firefox+Crashes'},
                {'title': 'Firefox crashes when you open it',
                 'url': '/kb/Firefox+crashes+when+you+open+it'},
                {'title': 'Firefox crashes when loading certain pages',
                 'url': '/kb/Firefox+crashes+when+loading+certain+pages'},
                {'title': 'Firefox crashes when you exit it',
                 'url': '/kb/Firefox+crashes+when+you+exit+it'},
                {'title': 'The Adobe Flash plugin has crashed',
                 'url': '/kb/The+Adobe+Flash+plugin+has+crashed'},
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
                 'url': '/kb/Bookmarks'},
                {'title': 'Lost Bookmarks',
                 'url': '/kb/Lost%20Bookmarks'},
                {'title': 'What happened to the bookmarks bar',
                 'url': '/kb/what-happened-bookmarks-toolbar'},
                {'title': 'Deleting Cookies',
                 'url': '/kb/Deleting+cookies'},
                {'title': 'Enabling and disabling cookies',
                 'url': '/kb/Enabling+and+disabling+cookies'},
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
                 'url': '/kb/what-firefox-sync'},
                {'title': 'What are App Tabs?',
                 'url': '/kb/what-are-app-tabs'},
                {'title': 'What is Panorama (also known as Tab Groups)?',
                 'url': '/kb/what-panorama'},
                {'title': 'What is the Add-on Bar?',
                 'url': '/kb/what-add-bar'},
                {'title': 'How do I use Private Browsing?',
                 'url': '/kb/Private+Browsing'},
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
                    'href="/kb/Uninstalling+add-ons">Uninstalling '
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
                 'url': '/kb/what-happened-status-bar'},
                {'title': 'What is plugin-container',
                 'url': '/kb/What+is+plugin-container'},
                {'title': 'Menu bar is mising',
                 'url': '/kb/Menu+bar+is+missing'},
            ],
            'tags': ['general'],
        }),
        ('b6', {
            'name': _lazy(u'I have suggestions for future versions of Firefox'),
            'html': 'If you\'re using the latest version of Firefox 4, you can '
                    'leave us suggestions for features at '
                    '<a href="//input.mozilla.com/feedback/">'
                    'Firefox Input</a>.',
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
            ('m0', {
                'name': _lazy(u"I can't install Firefox for Mobile."),
                'articles': [
                    {'title': 'Will Firefox work on my mobile device?',
                     'url': '/kb/will-firefox-work-my-mobile-device'},
                    {'title': 'How do I install Firefox on a mobile device?',
                     'url': '/kb/install-firefox-mobile'},
                ],
                'tags': ['install'],
            }),
            ('m1', {
                'name': _lazy(u'Firefox for mobile is having problems with certain web sites'),
                'html': 'You can try using the <a href="https://addons.mozilla.org/mobile/addon/phony/">Phony extension</a> '
                        'and setting your user agent to Android. Or try one of the following:',
                'articles': [
                    {'title': 'How can I use Youtube in Firefox for Mobile?',
                     'url': '/kb/firefox-mobile-doesnt-support-flash'},
                ],
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
                    {'title': 'Getting started with Firefox for mobile.',
                     'url': '/kb/getting-started-firefox-mobile'},
                    {'title': 'How do I use the Awesome Screen?',
                     'url': '/kb/how-do-i-use-awesome-screen'},
                    {'title': 'How do I use tabs on mobile?',
                     'url': '/kb/how-do-i-use-tabs-mobile'},
                    {'title': 'How do I use bookmarks on mobile?',
                     'url': '/kb/how-do-i-use-bookmarks-mobile'},
                    {'title': 'How do I zoom in and out of a website?',
                     'url': '/kb/zoom-in-and-out'},
                    {'title': 'How do I find and install Add-ons?',
                     'url': '/kb/find-and-install-add-ons'},
                ],
                'tags': ['learning'],
            }),
            ('m3', {
                'name': _lazy(u'I have a problem with an extension or plugin'),
                'extra_fields': ['addon'],
                'articles': [
                    {'title': "Firefox for mobile doesn't support Flash",
                     'url': '/kb/firefox-mobile-doesnt-support-flash'},
                    {'title': 'How do I find and install Add-ons?',
                     'url': '/kb/find-and-install-add-ons'},
                ],
                'tags': ['addon'],
            }),
            ('m4', {
                'name': _lazy(u'I need help syncing desktop Firefox with mobile'),
                'articles': [
                    {'title': 'How do I sync Firefox between my desktop and mobile?',
                     'url': '/kb/sync-firefox-between-desktop-and-mobile'},
                    {'title': "I've lost my phone - how do I deactivate Sync?",
                     'url': '/kb/ive-lost-my-phone-how-do-i-deactivate-sync'},
                    {'title': 'I have another question about sync',
                     'url': '/questions/new?product=sync'},
                ],
                'tags': ['sync'],
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
                     'url': '/kb/will-firefox-work-my-phone'},
                    {'title': 'How to install Firefox on N900',
                     'url': '/kb/install-firefox-mobile'},
                    {'title': 'How to find and install add-ons',
                     'url': '/kb/find-and-install-add-ons'},
                    {'title': 'How do I sync Firefox between my desktop and mobile?',
                     'url': '/kb/sync-firefox-between-desktop-and-mobile'},
                    {'title': 'How do I remove or disable Add-ons?',
                     'url': '/kb/remove-or-disable-add-ons'},
                    {'title': 'How do I change preferences?',
                     'url': '/kb/change-preferences'},
                ],
                'tags': ['general'],
            }),
            ('m6', {
                'name': _lazy(u'I have suggestions for how to improve Firefox for mobile'),
                'html': '<p>Please use our feedback system for suggestions for new Firefox features: '
                        '<a href="//input.mozilla.com/release/feedback">'
                        'Firefox Input</a></p>',
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
                     'url': '/kb/How+to+set+up+Firefox+Home+on+your+iPhone'},
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
                     'url': '/kb/How+to+sync+Firefox+settings+between+computers'},
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
                        '<a href="//firefoxformobile.uservoice.com/forums/67057-firefox-home-ideas">'
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
                     'url': '/kb/sync-firefox-between-desktop-and-mobile'},
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
                     'url': '/kb/How+to+set+up+Firefox+Home+on+your+iPhone'},
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
                     'url': '/kb/How+to+sync+Firefox+settings+between+computers'},
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
                     'url': '/kb/Firefox+Sync+is+not+working'},
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
                ' <a href="//www.mozilla.org/support">Mozilla Support</a>.',
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
