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
        ('d1', {
            'name': _lazy(u'Problems with certain web sites'),
            'extra_fields': ['sites_affected'],
            'html': 'We have lots of helpful articles on <em>problems with web'
                    ' sites</em> and hundreds of questions in our database. '
                    'Try one of the following:',
            'articles': [
                {'title': 'Errors when loading web sites',
                 'url': '/kb/Error%20loading%20web%20sites'},
                {'title': 'Firefox cannot load websites but other programs '
                          'can',
                 'url': '/kb/Firefox%20cannot%20load%20websites%20but%20other'
                        '%20programs%20can'},
                {'title': 'Web sites look wrong',
                 'url': '/kb/Websites%20look%20wrong'},
                {'title': 'Websites say cookies are blocked',
                 'url': '/kb/Websites%20say%20cookies%20are%20blocked'},
                {'title': 'Cannot connect after upgrading Firefox',
                 'url': '/kb/Cannot%20connect%20after%20upgrading%20Firefox'},
                {'title': 'Problems using Facebook in Firefox',
                 'url': '/kb/Problems+using+Facebook+in+Firefox'},
            ],
            'tags': ['websites'],
        }),
        ('d2', {
            'name': _lazy(u'Crashing or closing unexpectedly'),
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
                {'title': 'The Adobe Flash plugin has crashed',
                 'url': '/kb/The+Adobe+Flash+plugin+has+crashed'},
                {'title': 'How do I avoid crashes?',
                 'url': '/kb/avoid-crashes'},

            ],
            'tags': ['crash'],
        }),
        ('d3', {
            'name': _lazy(u'Bookmarks, cookies, history or settings'),
            'html': 'We have lots of helpful articles on <em>bookmarks, '
                    'cookies, history or settings</em> and hundreds of '
                    'questions in our database. Try one of the following:',
            'articles': [
                {'title': 'How do I use bookmarks?',
                 'url': '/kb/how-do-i-use-bookmarks'},
                {'title': 'Lost Bookmarks',
                 'url': '/kb/Lost%20Bookmarks'},
                {'title': 'Clear Recent History',
                 'url': '/kb/Clear%20Recent%20History'},
                {'title': 'Deleting Cookies',
                 'url': '/kb/Deleting+cookies'},
                {'title': 'Enabling and disabling cookies',
                 'url': '/kb/Enabling+and+disabling+cookies'},
                {'title': 'The bookmarks and history system will not be '
                          'functional',
                 'url': '/kb/The%20bookmarks%20and%20history%20system%20will'
                        '%20not%20be%20functional'},
            ],
            'tags': ['data'],
        }),
        ('d4', {
            'name': _lazy(u'Other Firefox features'),
            'html': 'We have lots of helpful articles to get you started <em>'
                    'learning and using Firefox</em> and hundreds of questions'
                    ' in our database. Try one of the following:',
            'articles': [
                {'title': 'How to set the home page',
                 'url': '/kb/How%20to%20set%20the%20home%20page'},
                {'title': 'How do I use Private Browsing?',
                 'url': '/kb/Private+Browsing'},
                {'title': 'How do I customize the toolbars?',
                 'url': '/kb/how-do-i-customize-toolbars'},
                {'title': 'What are App Tabs?',
                 'url': '/kb/what-are-app-tabs'},
                {'title': 'Pop-up blocker',
                 'url': '/kb/Pop-up%20blocker'},
                {'title': 'How do I add a device to Firefox Sync?',
                 'url': '/kb/add-a-device-to-firefox-sync'},
                {'title': 'Firefox does not ask to save tabs and windows on '
                          'exit',
                 'url': '/kb/Firefox%20does%20not%20ask%20to%20save%20tabs%20'
                        'and%20windows%20on%20exit'},
            ],
            'tags': ['features'],
        }),
        ('d5', {
            'name': _lazy(u'Problem with an extension or plugin'),
            'extra_fields': ['addon'],
            'html': 'Most extensions or plugins are not written by Mozilla '
                    'and you will need to contact the people or company who '
                    'made the extension/plugin for support. You can also try '
                    'one of the follow articles:',
            'articles': [
                {'title': 'Plugin crash reports',
                 'url': '/kb/Plugin%20crash%20reports'},
                {'title': 'Using the Windows Media Player plugin with Firefox',
                 'url': '/kb/Using%20the%20Windows%20Media%20Player%20plugin'
                        '%20with%20Firefox'},
                {'title': 'Add-ons are disabled after updating Firefox',
                 'url': '/kb/Add-ons%20are%20disabled%20after%20updating%20'
                        'Firefox'},
                {'title': 'The Adobe Flash plugin has crashed',
                 'url': '/kb/The%20Adobe%20Flash%20plugin%20has%20crashed'},
                {'title': 'Uninstalling add-ons',
                 'url': '/kb/Uninstalling+add-ons'},
                {'title': 'Troubleshooting extensions',
                 'url': '/kb/Troubleshooting%20extensions%20and%20themes'},
                {'title': 'Troubleshooting plugins',
                 'url': '/kb/Troubleshooting%20plugins'},
            ],
            'tags': ['addon'],
        }),
        ('d6', {
            'name': _lazy(u'Another kind of problem with Firefox'),
            'extra_fields': ['frequency', 'started'],
            'html': 'We have lots of helpful articles on <em>general Firefox '
                    'issues</em> and hundreds of questions in our database. '
                    'Try one of the following:',
            'articles': [
                {'title': 'Common questions after updating Firefox',
                 'url': '/kb/common-questions-after-updating-firefox'},
                {'title': 'Add-ons are disabled after updating Firefox',
                 'url': '/kb/Add-ons%20are%20disabled%20after%20updating%20'
                        'Firefox'},
                {'title': 'Firefox does not ask to save tabs and windows on '
                          'exit',
                 'url': '/kb/Firefox%20does%20not%20ask%20to%20save%20tabs%20'
                        'and%20windows%20on%20exit'},
                {'title': 'Menu bar is missing',
                 'url': '/kb/Menu+bar+is+missing'},
            ],
            'tags': ['other'],
        }),
        ('d7', {
            'name': _lazy(u'Suggestions for future versions of Firefox'),
            'html': 'You can give '
                    'us feedback about Firefox and let us know if you have '
                    'suggestions for future versions of Firefox at '
                    '<a href="//input.mozilla.com/feedback/">Firefox '
                    'Input</a>.',
            'deadend': True,
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
            ('m1', {
                'name': _lazy(u"Websites don't work"),
                'html': 'You can try using the <a href="https://addons.mozilla'
                        '.org/mobile/addon/phony/">Phony extension</a> '
                        'and setting your user agent to Android. Or try one '
                        'of the following:',
                'articles': [
                    {'title': 'How can I use Youtube in Firefox for Mobile?',
                     'url': '/kb/firefox-mobile-doesnt-support-flash'},
                    {'title': "Firefox for mobile doesn't support Flash",
                     'url': '/kb/firefox-mobile-doesnt-support-flash'},
                    {'title': 'How do I find and install Add-ons?',
                     'url': '/kb/find-and-install-add-ons'},
                    {'title': 'How do I zoom in and out of a website?',
                     'url': '/kb/zoom-in-and-out'},
                ],
                'extra_fields': ['sites_affected'],
                'tags': ['websites'],
            }),
            ('m2', {
                'name': _lazy(u'Installation'),
                'articles': [
                    {'title': 'Will Firefox work on my mobile device?',
                     'url': '/kb/will-firefox-work-my-mobile-device'},
                    {'title': 'How do I install Firefox on a mobile device?',
                     'url': '/kb/install-firefox-mobile'},
                ],
                'tags': ['install'],
            }),
            ('m3', {
                'name': _lazy(u'Features'),
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
                'tags': ['features'],
            }),
            ('m4', {
                'name': _lazy(u'Plugins, add-ons or extensions'),
                'extra_fields': ['addon'],
                'articles': [
                    {'title': "Firefox for mobile doesn't support Flash",
                     'url': '/kb/firefox-mobile-doesnt-support-flash'},
                    {'title': 'How do I find and install Add-ons?',
                     'url': '/kb/find-and-install-add-ons'},
                ],
                'tags': ['addon'],
            }),
            ('m5', {
                'name': _lazy(u'Syncing desktop and mobile'),
                'articles': [
                    {'title': 'How do I sync Firefox between my desktop and '
                              'mobile?',
                     'url': '/kb/sync-firefox-between-desktop-and-mobile'},
                    {'title': "I've lost my phone - how do I deactivate Sync?",
                     'url': '/kb/ive-lost-my-phone-how-do-i-deactivate-sync'},
                    {'title': 'Ask a new question about Sync',
                     'url': '/questions/new?product=sync'},
                ],
                'tags': ['sync'],
            }),
            ('m6', {
                'name': _lazy(u'Other issues'),
                'extra_fields': ['frequency'],
                'html': 'We have lots of helpful articles on <em>general '
                        'issues with Firefox for mobile</em> and hundreds '
                        'of questions in our database. Try one of the '
                        'following:',
                'articles': [
                    {'title': 'How to find and install add-ons',
                     'url': '/kb/find-and-install-add-ons'},
                    {'title': 'How do I sync Firefox between my desktop and '
                              'mobile?',
                     'url': '/kb/sync-firefox-between-desktop-and-mobile'},
                    {'title': "Firefox for mobile doesn't support Flash",
                     'url': '/kb/firefox-mobile-doesnt-support-flash'},
                    {'title': 'How can I use Youtube in Firefox for Mobile?',
                     'url': '/kb/firefox-mobile-doesnt-support-flash'},
                ],
                'tags': ['other'],
            }),
            ('m7', {
                'name': _lazy(u'Suggestions to improve Firefox'),
                'html': '<p>Please use our feedback system for suggestions '
                        'for new Firefox features: '
                        '<a href="//m.input.mozilla.com/en-US/feedback">'
                        'Firefox Input</a></p>',
                'deadend': True,
            }),
        ])
    }),
    ('home', {
        'name': _lazy(u'Firefox Home'),
        'subtitle':  _lazy(u'iPhone and iPad'),
        'tags': ['FxHome'],
        'categories': SortedDict([
            ('i1', {
                'name': _lazy(u"Setting up Firefox Home on my iPhone"),
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
                'name': _lazy(u'Not all my data is syncing between Firefox '
                          'and Firefox Home or other problems'),
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
                    {'title': 'Firefox Sync is not working',
                     'url': '/kb/Firefox%20Sync%20is%20not%20working'}
                ],
                'tags': ['other'],
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
                    {'title': 'How do I sync Firefox between my desktop and '
                              'mobile?',
                     'url': '/kb/sync-firefox-between-desktop-and-mobile'},
                    {'title': 'How do I add a device to Firefox Sync?',
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
                    {'title': 'How to set up Firefox Home on your iPhone',
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
                    {'title': 'How to sync Firefox settings between computers',
                     'url': '/kb/How%20to%20sync%20Firefox%20settings%20'
                            'between%20computers'},
                    {'title': 'How do I set up Firefox Sync?',
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
                    {'title': 'Firefox Sync is not working',
                     'url': '/kb/Firefox+Sync+is+not+working'},
                    {'title': 'Firefox Home does not work ',
                     'url': '/kb/Firefox+Home+does+not+work'},
                    {'title': 'Cannot log in to Firefox Home App ',
                     'url': '/kb/Cannot+log+in+to+Firefox+Home+App'},
                    {'title': 'Replace your Sync information',
                     'url': '/kb/Replace+your+Sync+information'},
                ],
                'tags': ['other'],
            }),
        ])
    }),
    ('other', {
        'name': _lazy(u"Thunderbird"),
        'subtitle':  _lazy(u"or other Mozilla products"),
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
