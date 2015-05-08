# Bundles for JS/CSS Minification

PIPELINE_CSS = {
    'common': {
        'source_filenames': (
            'normalize-css/normalize.css',
            'less/main.less',
            'less/search.less',
        ),
        'output_filename': 'common-min.css'
    },
    'community': {
        'source_filenames': (
            'less/wiki-content.less',
            'less/community.less',
            'less/select.less',
        ),
        'output_filename': 'community-min.css'
    },
    'community-new': {
        'source_filenames': (
            'fontawesome/css/font-awesome.css',
            'pikaday/css/pikaday.css',
            'less/wiki-content.less',
            'less/community-new.less',
        ),
        'output_filename': 'community-new-min.css'
    },
    'mobile-common': {
        'source_filenames': (
            'normalize-css/normalize.css',
            'less/mobile/main.less',
        ),
        'output_filename': 'mobile-common-min.css'
    },
    'print': {
        'source_filenames': (
            'css/print.css',
        ),
        'output_filename': 'print-min.css',
        'extra_context': {
            'media': 'print',
        }
    },
    # TODO: remove dependency on jquery ui CSS and use our own
    'jqueryui': {
        'source_filenames': (
            'css/jqueryui/jqueryui.css',
        ),
        'output_filename': 'jqueryui-min.css'
    },
    'forums': {
        'source_filenames': (
            'less/forums.less',
            'less/reportabuse.less',
        ),
        'output_filename': 'forums-min.css'
    },
    'questions': {
        'source_filenames': (
            'less/questions.less',
            'css/cannedresponses.css',
            'less/reportabuse.less',
        ),
        'output_filename': 'questions-min.css'
    },
    'questions.metrics': {
        'source_filenames': (
            'less/questions.metrics.less',
        ),
        'output_filename': 'questions.metrics-min.css'
    },
    'mobile-questions': {
        'source_filenames': (
            'less/mobile/questions.less',
        ),
        'output_filename': 'mobile-questions-min.css'
    },
    'mobile-aaq': {
        'source_filenames': (
            'less/mobile/aaq.less',
        ),
        'output_filename': 'mobile-aaq-min.css'
    },
    'rickshaw': {
        'source_filenames': (
            'css/jqueryui/jqueryui.css',
            'css/rickshaw.css',
            'less/rickshaw.sumo.less',
        ),
        'output_filename': 'rickshaw-min.css'
    },
    'mobile-search': {
        'source_filenames': (
            'less/mobile/search.less',
        ),
        'output_filename': 'mobile-search-min.css'
    },
    'wiki': {
        'source_filenames': (
            'css/users.autocomplete.css',
            'css/users.list.css',
            'less/wiki.less',
            'less/wiki-content.less',
            'css/screencast.css',
        ),
        'output_filename': 'wiki-min.css'
    },
    'mobile-wiki': {
        'source_filenames': (
            'less/mobile/wiki.less',
            'less/wiki-content.less',
        ),
        'output_filename': 'mobile-wiki-min.css'
    },
    'mobile-wiki-minimal': {
        'source_filenames': (
            'normalize-css/normalize.css',
            'less/mobile/main.less',
            'less/mobile/wiki.less',
            'less/wiki-content.less',
        ),
        'output_filename': 'mobile-wiki-minimal-min.css'
    },
    'home': {
        'source_filenames': (
            'less/home.less',
        ),
        'output_filename': 'home-min.css'
    },
    'gallery': {
        'source_filenames': (
            'less/gallery.less',
        ),
        'output_filename': 'gallery-min.css'
    },
    'ie': {
        'source_filenames': (
            'css/ie.css',
            'css/ie8.css',
        ),
        'output_filename': 'ie-min.css'
    },
    'ie8': {
        'source_filenames': (  # IE 8 needs some specific help.
            'css/ie8.css',
        ),
        'output_filename': 'ie8-min.css'
    },
    'customercare': {
        'source_filenames': (
            'less/customercare.less',
        ),
        'output_filename': 'customercare-min.css'
    },
    'users': {
        'source_filenames': (
            'less/users.less',
            'less/reportabuse.less',
        ),
        'output_filename': 'users-min.css'
    },
    'mobile-users': {
        'source_filenames': (
            'less/mobile/users.less',
        ),
        'output_filename': 'mobile-users-min.css'
    },
    'monitor': {
        'source_filenames': (
            'css/monitor.css',
        ),
        'output_filename': 'monitor-min.css'
    },
    'messages': {
        'source_filenames': (
            'css/users.autocomplete.css',
            'less/messages.less',
        ),
        'output_filename': 'messages-min.css'
    },
    'mobile-messages': {
        'source_filenames': (
            'less/mobile/messages.less',
        ),
        'output_filename': 'mobile-messages-min.css'
    },
    'products': {
        'source_filenames': (
            'less/products.less',
        ),
        'output_filename': 'products-min.css'
    },
    'mobile-products': {
        'source_filenames': (
            'less/mobile/products.less',
        ),
        'output_filename': 'mobile-products-min.css'
    },
    'groups': {
        'source_filenames': (
            'css/users.autocomplete.css',
            'css/users.list.css',
            'css/groups.css',
            'css/wiki_syntax.css',
        ),
        'output_filename': 'groups-min.css'
    },
    'kpi.dashboard': {
        'source_filenames': (
            'less/kpi.dashboard.less',
        ),
        'output_filename': 'kpi.dashboard-min.css'
    },
    'locale-switcher': {
        'source_filenames': (
            'less/locale-switcher.less',
        ),
        'output_filename': 'locale-switcher-min.css'
    },
    'mobile-locale-switcher': {
        'source_filenames': (
            'less/mobile/locales.less',
        ),
        'output_filename': 'mobile-locale-switcher-min.css'
    },
    'kbdashboards': {
        'source_filenames': (
            'less/kbdashboards.less',
        ),
        'output_filename': 'kbdashboards-min.css'
    },
    'landings-get-involved': {
        'source_filenames': (
            'less/landings/get-involved.less',
        ),
        'output_filename': 'landings-get-involved-min.css'
    },
    'mobile-landings-get-involved': {
        'source_filenames': (
            'less/mobile/landings/get-involved.less',
        ),
        'output_filename': 'mobile-landings-get-involved-min.css'
    },
    'badges': {
        'source_filenames': (
            'less/badges.less',
        ),
        'output_filename': 'badges-min.css'
    }
}

PIPELINE_JS = {
    'common': {
        'source_filenames': (
            'js/i18n.js',
            'underscore/underscore.js',
            'moment/moment.js',
            'jquery/jquery.min.js',
            'jquery/jquery-migrate.js',
            'js/libs/jquery.cookie.js',
            'js/libs/jquery.placeholder.js',
            'js/templates/macros.js',
            'js/templates/search-results-list.js',
            'js/templates/search-results.js',
            'nunjucks/browser/nunjucks-slim.js',
            'js/nunjucks.js',
            'js/cached_xhr.js',
            'js/search_utils.js',
            'js/browserdetect.js',
            'js/libs/uitour.js',
            'js/kbox.js',
            'js/main.js',
            'js/format.js',
            'modernizr/modernizr.js',
            'js/geoip-locale.js',
            'mailcheck/src/mailcheck.js',
            'js/ui.js',
            'js/analytics.js',
            'js/surveygizmo.js',
            'js/instant_search.js',
        ),
        'output_filename': 'common-min.js'
    },
    'community': {
        'source_filenames': (
            'jquery/jquery.min.js',
            'jquery/jquery-migrate.js',
            'js/community.js',
            'js/select.js',
        ),
        'output_filename': 'community-min.js'
    },
    'community-new-questions': {
        'source_filenames': (
            # This uses the minified version because it is optimized to leave
            # out lots of debug stuff, so it is significantly smaller than
            # just minifying react.js.
            # TODO: Figure out how to include the full sized version in dev,
            # because it produces much nicer error messages.
            'react/react.min.js',
            # 'react/react.js',
            'pikaday/pikaday.js',
            'js/community-questions.browserify.js',
        ),
        'output_filename': 'community-questions-min.js'
    },
    'community-new-l10n': {
        'source_filenames': (
            # This uses the minified version because it is optimized to leave
            # out lots of debug stuff, so it is significantly smaller than
            # just minifying react.js.
            # TODO: Figure out how to include the full sized version in dev,
            # because it produces much nicer error messages.
            'react/react.min.js',
            # 'react/react.js',
            'pikaday/pikaday.js',
            'js/community-l10n.browserify.js',
        ),
        'output_filename': 'community-l10n-min.js'
    },
    'mobile-common': {
        'source_filenames': (
            'js/i18n.js',
            'underscore/underscore.js',
            'jquery/jquery.min.js',
            'jquery/jquery-migrate.js',
            'modernizr/modernizr.js',
            'js/browserdetect.js',
            'js/aaq.js',
            'js/mobile/ui.js',
            'js/analytics.js',
        ),
        'output_filename': 'mobile-common-min.js'
    },
    'ie6-8': {
        'source_filenames': (
            'nwmatcher/src/nwmatcher.js',
            'js/libs/selectivizr-1.0.2.js',
        ),
        'output_filename': 'ie6-8-min.js'
    },
    'jqueryui': {
        'source_filenames': (
            'jquery-ui/ui/jquery.ui.core.js',
            'jquery-ui/ui/jquery.ui.widget.js',
            'jquery-ui/ui/jquery.ui.mouse.js',
            'jquery-ui/ui/jquery.ui.position.js',
            'jquery-ui/ui/jquery.ui.sortable.js',
            'jquery-ui/ui/jquery.ui.accordion.js',
            'jquery-ui/ui/jquery.ui.autocomplete.js',
            'jquery-ui/ui/jquery.ui.datepicker.js',
            'jquery-ui/ui/jquery.ui.menu.js',
            'jquery-ui/ui/jquery.ui.slider.js',
            'jquery-ui/ui/jquery.ui.tabs.js',
        ),
        'output_filename': 'jqueryui-min.js'
    },
    'questions': {
        'source_filenames': (
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
        'output_filename': 'questions-min.js'
    },
    'questions.metrics': {
        'source_filenames': (
            'js/questions.metrics-dashboard.js',
        ),
        'output_filename': 'questions.metrics-min.js'
    },
    'mobile-questions': {
        'source_filenames': (
            'js/mobile/questions.js',
            'js/questions.metrics.js',
        ),
        'output_filename': 'mobile-questions-min.js'
    },
    'mobile-aaq': {
        'source_filenames': (
            'js/aaq.js',
            'js/mobile/aaq.js',
        ),
        'output_filename': 'mobile-aaq-min.js'
    },
    'products': {
        'source_filenames': (
            'js/compare_versions.js',
            'js/products.js',
        ),
        'output_filename': 'products-min.js'
    },
    'search': {
        'source_filenames': (
            'js/search.js',
        ),
        'output_filename': 'search-min.js'
    },
    'forums': {
        'source_filenames': (
            'js/markup.js',
            'js/ajaxpreview.js',
            'js/forums.js',
            'js/reportabuse.js',
        ),
        'output_filename': 'forums-min.js'
    },
    'gallery': {
        'source_filenames': (
            'js/libs/jquery.ajaxupload.js',
            'js/gallery.js',
        ),
        'output_filename': 'gallery-min.js'
    },
    'wiki': {
        'source_filenames': (
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
            'js/templates/wiki-related-doc.js',
            'js/templates/wiki-search-results.js',
            'js/wiki_search.js',
        ),
        'output_filename': 'wiki-min.js'
    },
    'rickshaw': {
        'source_filenames': (
            'd3/d3.js',
            'js/libs/d3.layout.min.js',
            'js/libs/rickshaw.js',
            'js/rickshaw_utils.js',
        ),
        'output_filename': 'rickshaw-min.js'
    },
    'mobile-wiki': {
        'source_filenames': (
            'underscore/underscore.js',
            'js/libs/jquery.cookie.js',
            'js/libs/jquery.lazyload.js',
            'js/browserdetect.js',
            'js/showfor.js',
            'js/ajaxform.js',
            'js/mobile/wiki.js',
            'js/wiki.metrics.js',
        ),
        'output_filename': 'mobile-wiki-min.js'
    },
    'mobile-wiki-minimal': {
        'source_filenames': (
            'js/i18n.js',
            'underscore/underscore.js',
            'jquery/jquery.min.js',
            'jquery/jquery-migrate.js',
            'modernizr/modernizr.js',
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
        'output_filename': 'mobile-wiki-minimal-min.js'
    },
    'wiki.history': {
        'source_filenames': (
            'js/historycharts.js',
        ),
        'output_filename': 'wiki.history-min.js'
    },
    'wiki.diff': {
        'source_filenames': (
            'js/libs/diff_match_patch_uncompressed.js',
            'js/diff.js',
        ),
        'output_filename': 'wiki.diff-min.js'
    },
    'wiki.editor': {
        'source_filenames': (
            'ace/src/ace.js',
            'ace/src/ext-language_tools.js',
            'js/ace.mode-sumo.js',
        ),
        'output_filename': 'wiki.editor-min.js'
    },
    'wiki.dashboard': {
        'source_filenames': (
            'js/wiki.dashboard.js',
        ),
        'output_filename': 'wiki.dashboard-min.js'
    },
    'customercare': {
        'source_filenames': (
            'js/libs/jquery.cookie.js',
            'js/libs/jquery.bullseye-1.0.min.js',
            'js/libs/twitter-text.js',
            'js/customercare.js',
            'js/users.js',
        ),
        'output_filename': 'customercare-min.js'
    },
    'users': {
        'source_filenames': (
            'js/users.js',
            'js/reportabuse.js',
        ),
        'output_filename': 'users-min.js'
    },
    'messages': {
        'source_filenames': (
            'js/markup.js',
            'js/libs/jquery.autoresize.js',
            'js/libs/jquery.tokeninput.js',
            'js/users.autocomplete.js',
            'js/ajaxpreview.js',
            'js/messages.js',
        ),
        'output_filename': 'messages-min.js'
    },
    'mobile-messages': {
        'source_filenames': (
            'js/libs/jquery.tokeninput.js',
            'js/users.autocomplete.js',
        ),
        'output_filename': 'mobile-messages-min.js'
    },
    'groups': {
        'source_filenames': (
            'js/libs/jquery.tokeninput.js',
            'js/users.autocomplete.js',
            'js/markup.js',
            'js/groups.js',
            'js/editable.js',
        ),
        'output_filename': 'groups-min.js'
    },
    'kpi.dashboard': {
        'source_filenames': (
            'js/kpi.dashboard.js',
        ),
        'output_filename': 'kpi.dashboard-min.js'
    }
}
