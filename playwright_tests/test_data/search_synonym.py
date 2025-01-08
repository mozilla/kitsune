class SearchSynonyms:

    synonym_dict = {
        # Media
        'music': ['media', 'audio', 'sound', 'mp3', 'song'],

        # Technical terms
        'cache': ['cash', 'cookies'],
        'popup': ['pop up'],
        'pop up': ['popup'],
        'popups': ['pop-up', 'pop-ups', 'pop ups', 'pops up'],

        # Actions
        'clear': ['delete', 'remove', 'deleting'],

        # Brands
        'firefox': ['browser'],
        'modzilla': ['mozilla'],
        'mozzila': ['mozilla'],
        'mozzilla': ['mozilla'],
        'mozila': ['mozilla'],
        'ios': ['ipad', 'iphone', 'ipod'],
        'ipad': ['ios', 'iphone', 'ipod'],
        'iphone': ['ios', 'ipad', 'ipod'],
        'ipod': ['ios', 'ipad', 'iphone'],

        # Product features
        'addon': ['extension', 'theme'],
        'add-on': ['extension', 'theme'],
        'add-ons': ['extensions', 'themes', "addon"],
        'theme': ['addon', 'extension', 'add-on'],
        'homepage': ['home page', 'home screen', 'homescreen', 'awesome screen', 'firefox hub',
                     'start screen'],
        'search bar': ['search field', 'search strip', 'search box']
    }
