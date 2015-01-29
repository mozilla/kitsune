# Bundles for JS/CSS Minification
MINIFY_BUNDLES = {
    'css': {
        'common': (
            'css/normalize.css',
            'less/main.less',
            'less/search.less',
        ),
        'community': (
            'less/wiki-content.less',
            'less/community.less',
            'less/select.less',
        ),
        'mobile/common': (
            'css/normalize.css',
            'less/mobile/main.less',
        ),
        'print': (
            'css/print.css',
        ),
        # TODO: remove dependency on jquery ui CSS and use our own
        'jqueryui/jqueryui': (
            'css/jqueryui/jqueryui.css',
        ),
        'forums': (
            'less/forums.less',
            'less/reportabuse.less',
        ),
        'questions': (
            'less/questions.less',
            'css/cannedresponses.css',
            'less/reportabuse.less',
        ),
        'questions.metrics': (
            'less/questions.metrics.less',
        ),
        'mobile/questions': (
            'less/mobile/questions.less',
        ),
        'mobile/aaq': (
            'less/mobile/aaq.less',
        ),
        'rickshaw': (
            'css/jqueryui/jqueryui.css',
            'css/rickshaw.css',
            'less/rickshaw.sumo.less',
        ),
        'mobile/search': (
            'less/mobile/search.less',
        ),
        'wiki': (
            'css/users.autocomplete.css',
            'css/users.list.css',
            'less/wiki.less',
            'less/wiki-content.less',
            'css/screencast.css',
        ),
        'mobile/wiki': (
            'less/mobile/wiki.less',
            'less/wiki-content.less',
        ),
        'mobile/wiki-minimal': (
            'css/normalize.css',
            'less/mobile/main.less',
            'less/mobile/wiki.less',
            'less/wiki-content.less',
        ),
        'home': (
            'less/home.less',
        ),
        'gallery': (
            'less/gallery.less',
        ),
        'ie': (
            'css/ie.css',
            'css/ie8.css',
        ),
        'ie8': (  # IE 8 needs some specific help.
            'css/ie8.css',
        ),
        'customercare': (
            'less/customercare.less',
        ),
        'users': (
            'less/users.less',
            'less/reportabuse.less',
        ),
        'mobile/users': (
            'less/mobile/users.less',
        ),
        'monitor': (
            'css/monitor.css',
        ),
        'messages': (
            'css/users.autocomplete.css',
            'less/messages.less',
        ),
        'mobile/messages': (
            'less/mobile/messages.less',
        ),
        'products': (
            'less/products.less',
        ),
        'mobile/products': (
            'less/mobile/products.less',
        ),
        'groups': (
            'css/users.autocomplete.css',
            'css/users.list.css',
            'css/groups.css',
            'css/wiki_syntax.css',
        ),
        'kpi.dashboard': (
            'less/kpi.dashboard.less',
        ),
        'locale-switcher': (
            'less/locale-switcher.less',
        ),
        'mobile/locale-switcher': (
            'less/mobile/locales.less',
        ),
        'kbdashboards': (
            'less/kbdashboards.less',
        ),
        'landings/get-involved': (
            'less/landings/get-involved.less',
        ),
        'mobile/landings/get-involved': (
            'less/mobile/landings/get-involved.less',
        ),
        'badges': (
            'less/badges.less',
        ),
    },
    'js': {
        'common': (
            'js/i18n.js',
            'js/libs/underscore.js',
            'js/libs/moment-2.8.3.js',
            'js/libs/jquery-1.10.1.min.js',
            'js/libs/jquery.migrate.js',
            'js/libs/jquery.cookie.js',
            'js/libs/jquery.placeholder.js',
            'js/templates/macros.js',
            'js/templates/search-results-list.js',
            'js/templates/search-results.js',
            'js/libs/nunjucks-slim.js',
            'js/nunjucks.js',
            'js/cached_xhr.js',
            'js/search_utils.js',
            'js/browserdetect.js',
            'js/libs/uitour.js',
            'js/kbox.js',
            'js/main.js',
            'js/format.js',
            'js/libs/modernizr-2.6.1.js',
            'js/geoip-locale.js',
            'js/libs/mailcheck.js',
            'js/ui.js',
            'js/analytics.js',
            'js/surveygizmo.js',
            'js/instant_search.js',
        ),
        'community': (
            'js/libs/jquery-1.10.1.min.js',
            'js/community.js',
            'js/select.js',
        ),
        'mobile/common': (
            'js/i18n.js',
            'js/libs/underscore.js',
            'js/libs/jquery-1.10.1.min.js',
            'js/libs/jquery.migrate.js',
            'js/libs/modernizr-2.6.1.js',
            'js/browserdetect.js',
            'js/aaq.js',
            'js/mobile/ui.js',
            'js/analytics.js',
        ),
        'ie6-8': (
            'js/libs/nwmatcher-1.2.5.js',
            'js/libs/selectivizr-1.0.2.js',
        ),
        'libs/jqueryui': (
            'js/libs/jqueryui.js',
        ),
        'questions': (
            'js/markup.js',
            'js/ajaxvote.js',
            'js/ajaxpreview.js',
            'js/remote.js',
            'js/aaq.js',
            'js/questions.js',
            'js/libs/jquery.tokeninput.js',
            'js/tags.filter.js',
            'js/tags.js',
            'js/reportabuse.js',
            'js/questions.metrics.js',
            'js/libs/jquery.ajaxupload.js',
            'js/upload.js',
        ),
        'questions.metrics': (
            'js/questions.metrics-dashboard.js',
        ),
        'mobile/questions': (
            'js/mobile/questions.js',
            'js/questions.metrics.js',
        ),
        'mobile/aaq': (
            'js/aaq.js',
            'js/mobile/aaq.js',
        ),
        'products': (
            'js/products.js',
        ),
        'search': (
            'js/search.js',
        ),
        'forums': (
            'js/markup.js',
            'js/ajaxpreview.js',
            'js/forums.js',
            'js/reportabuse.js',
        ),
        'gallery': (
            'js/libs/jquery.ajaxupload.js',
            'js/gallery.js',
        ),
        'wiki': (
            'js/markup.js',
            'js/libs/django/urlify.js',
            'js/libs/django/prepopulate.js',
            'js/libs/swfobject.js',
            'js/libs/jquery.lazyload.js',
            'js/libs/jquery.tokeninput.js',
            'js/users.autocomplete.js',
            'js/screencast.js',
            'js/showfor.js',
            'js/ajaxvote.js',
            'js/ajaxpreview.js',
            'js/wiki.js',
            'js/tags.js',
            'js/dashboards.js',
            'js/editable.js',
            'js/wiki.metrics.js',
        ),
        'rickshaw': (
            'js/libs/jqueryui.js',
            'js/libs/d3.js',
            'js/libs/d3.layout.min.js',
            'js/libs/rickshaw.js',
            'js/rickshaw_utils.js',
        ),
        'mobile/wiki': (
            'js/libs/underscore.js',
            'js/libs/jquery.cookie.js',
            'js/libs/jquery.lazyload.js',
            'js/browserdetect.js',
            'js/showfor.js',
            'js/ajaxform.js',
            'js/mobile/wiki.js',
            'js/wiki.metrics.js',
        ),
        'mobile/wiki-minimal': (
            'js/i18n.js',
            'js/libs/underscore.js',
            'js/libs/jquery-1.10.1.min.js',
            'js/libs/jquery.migrate.js',
            'js/libs/modernizr-2.6.1.js',
            'js/browserdetect.js',
            'js/mobile/ui.js',
            'js/analytics.js',
            'js/libs/jquery.cookie.js',
            'js/libs/jquery.lazyload.js',
            'js/showfor.js',
            'js/ajaxform.js',
            'js/mobile/wiki.js',
            'js/wiki.metrics.js',
        ),
        'wiki.history': (
            'js/historycharts.js',
        ),
        'wiki.diff': (
            'js/libs/diff_match_patch_uncompressed.js',
            'js/diff.js',
        ),
        'wiki.editor': (
            'js/libs/ace/ace.js',
            'js/libs/ace/ext-language_tools.js',
            'js/ace.mode-sumo.js',
        ),
        'wiki.dashboard': (
            'js/wiki.dashboard.js',
        ),
        'customercare': (
            'js/libs/jquery.cookie.js',
            'js/libs/jquery.bullseye-1.0.min.js',
            'js/libs/twitter-text.js',
            'js/customercare.js',
            'js/users.js',
        ),
        'users': (
            'js/users.js',
            'js/reportabuse.js',
        ),
        'messages': (
            'js/markup.js',
            'js/libs/jquery.autoresize.js',
            'js/libs/jquery.tokeninput.js',
            'js/users.autocomplete.js',
            'js/ajaxpreview.js',
            'js/messages.js',
        ),
        'mobile/messages': (
            'js/libs/jquery.tokeninput.js',
            'js/users.autocomplete.js',
        ),
        'groups': (
            'js/libs/jquery.tokeninput.js',
            'js/users.autocomplete.js',
            'js/markup.js',
            'js/groups.js',
            'js/editable.js',
        ),
        'kpi.dashboard': (
            'js/kpi.dashboard.js',
        ),
    },
}
