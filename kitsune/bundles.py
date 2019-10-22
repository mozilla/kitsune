# Bundles for JS/CSS Minification

PIPELINE_CSS = {
    'common': {
        'source_filenames': (
            'normalize-css/normalize.css',
            'sumo/less/main.less',
            'sumo/less/search.less',
            'mozilla-tabzilla/css/tabzilla.css',
        ),
        'output_filename': 'build/common-min.css'
    },
    'community': {
        'source_filenames': (
            'sumo/less/wiki-content.less',
            'community/less/community.less',
            'community/less/select.less',
        ),
        'output_filename': 'build/community-min.css'
    },
    'community-new': {
        'source_filenames': (
            'fontawesome/css/font-awesome.css',
            'pikaday/css/pikaday.css',
            'sumo/less/wiki-content.less',
            'community/less/community-new.less',
        ),
        'output_filename': 'build/community-new-min.css'
    },
    'mobile-common': {
        'source_filenames': (
            'fontawesome/css/font-awesome.css',
            'normalize-css/normalize.css',
            'sumo/less/mobile/main.less',
            'sumo/less/mobile/search.less',
        ),
        'output_filename': 'build/mobile-common-min.css'
    },
    'print': {
        'source_filenames': (
            'sumo/css/print.css',
        ),
        'output_filename': 'build/print-min.css',
        'extra_context': {
            'media': 'print',
        }
    },
    # TODO: remove dependency on jquery ui CSS and use our own
    'jqueryui': {
        'source_filenames': (
            'sumo/css/jqueryui/jqueryui.css',
        ),
        'output_filename': 'build/jqueryui-min.css'
    },
    'forums': {
        'source_filenames': (
            'sumo/less/forums.less',
            'sumo/less/reportabuse.less',
        ),
        'output_filename': 'build/forums-min.css'
    },
    'questions': {
        'source_filenames': (
            'sumo/less/questions.less',
            'sumo/css/cannedresponses.css',
            'sumo/less/reportabuse.less',
        ),
        'output_filename': 'build/questions-min.css'
    },
    'questions.metrics': {
        'source_filenames': (
            'sumo/less/questions.metrics.less',
        ),
        'output_filename': 'build/questions.metrics-min.css'
    },
    'questions.aaq.react': {
        'source_filenames': (
            'fontawesome/css/font-awesome.css',
            'questions/less/questions.aaq.react.less',
        ),
        'output_filename': 'build/questions.aaq.react-min.css'
    },
    'mobile-questions': {
        'source_filenames': (
            'sumo/less/mobile/questions.less',
        ),
        'output_filename': 'build/mobile-questions-min.css'
    },
    'mobile-aaq': {
        'source_filenames': (
            'sumo/less/mobile/aaq.less',
        ),
        'output_filename': 'build/mobile-aaq-min.css'
    },
    'rickshaw': {
        'source_filenames': (
            'sumo/css/jqueryui/jqueryui.css',
            'sumo/css/rickshaw.css',
            'sumo/less/rickshaw.sumo.less',
        ),
        'output_filename': 'build/rickshaw-min.css'
    },
    'mobile-search': {
        'source_filenames': (
            'sumo/less/mobile/search.less',
        ),
        'output_filename': 'build/mobile-search-min.css'
    },
    'wiki': {
        'source_filenames': (
            'sumo/css/users.autocomplete.css',
            'sumo/css/users.list.css',
            'sumo/less/wiki.less',
            'sumo/less/wiki-content.less',
            'sumo/css/screencast.css',
        ),
        'output_filename': 'build/wiki-min.css'
    },
    'wiki-editor': {
        'source_filenames': (
            'codemirror/lib/codemirror.css',
            'codemirror/addon/hint/show-hint.css',
        ),
        'output_filename': 'wiki-editor-min.css'
    },
    'mobile-wiki': {
        'source_filenames': (
            'sumo/less/mobile/wiki.less',
            'sumo/less/wiki-content.less',
        ),
        'output_filename': 'build/mobile-wiki-min.css'
    },
    'mobile-wiki-minimal': {
        'source_filenames': (
            'normalize-css/normalize.css',
            'sumo/less/mobile/main.less',
            'sumo/less/mobile/wiki.less',
            'sumo/less/wiki-content.less',
        ),
        'output_filename': 'build/mobile-wiki-minimal-min.css'
    },
    'home': {
        'source_filenames': (
            'sumo/less/home.less',
        ),
        'output_filename': 'build/home-min.css'
    },
    'gallery': {
        'source_filenames': (
            'sumo/less/gallery.less',
        ),
        'output_filename': 'build/gallery-min.css'
    },
    'ie': {
        'source_filenames': (
            'sumo/css/ie.css',
            'sumo/css/ie8.css',
        ),
        'output_filename': 'build/ie-min.css'
    },
    'ie8': {
        'source_filenames': (  # IE 8 needs some specific help.
            'sumo/css/ie8.css',
        ),
        'output_filename': 'build/ie8-min.css'
    },
    'customercare': {
        'source_filenames': (
            'sumo/less/customercare.less',
        ),
        'output_filename': 'build/customercare-min.css'
    },
    'users': {
        'source_filenames': (
            'sumo/less/users.less',
            'sumo/less/reportabuse.less',
        ),
        'output_filename': 'build/users-min.css'
    },
    'mobile-users': {
        'source_filenames': (
            'sumo/less/mobile/users.less',
        ),
        'output_filename': 'build/mobile-users-min.css'
    },
    'monitor': {
        'source_filenames': (
            'sumo/css/monitor.css',
        ),
        'output_filename': 'build/monitor-min.css'
    },
    'messages': {
        'source_filenames': (
            'sumo/css/users.autocomplete.css',
            'sumo/less/messages.less',
        ),
        'output_filename': 'build/messages-min.css'
    },
    'mobile-messages': {
        'source_filenames': (
            'sumo/less/mobile/messages.less',
        ),
        'output_filename': 'build/mobile-messages-min.css'
    },
    'products': {
        'source_filenames': (
            'sumo/less/products.less',
        ),
        'output_filename': 'build/products-min.css'
    },
    'mobile-products': {
        'source_filenames': (
            'sumo/less/mobile/products.less',
        ),
        'output_filename': 'build/mobile-products-min.css'
    },
    'groups': {
        'source_filenames': (
            'sumo/css/users.autocomplete.css',
            'sumo/css/users.list.css',
            'sumo/css/groups.css',
            'sumo/css/wiki_syntax.css',
        ),
        'output_filename': 'build/groups-min.css'
    },
    'kpi.dashboard': {
        'source_filenames': (
            'sumo/less/kpi.dashboard.less',
        ),
        'output_filename': 'build/kpi.dashboard-min.css'
    },
    'locale-switcher': {
        'source_filenames': (
            'sumo/less/locale-switcher.less',
        ),
        'output_filename': 'build/locale-switcher-min.css'
    },
    'mobile-locale-switcher': {
        'source_filenames': (
            'sumo/less/mobile/locales.less',
        ),
        'output_filename': 'build/mobile-locale-switcher-min.css'
    },
    'kbdashboards': {
        'source_filenames': (
            'sumo/less/kbdashboards.less',
        ),
        'output_filename': 'build/kbdashboards-min.css'
    },
    'landings-get-involved': {
        'source_filenames': (
            'sumo/less/landings/get-involved.less',
        ),
        'output_filename': 'build/landings-get-involved-min.css'
    },
    'mobile-landings-get-involved': {
        'source_filenames': (
            'sumo/less/mobile/landings/get-involved.less',
        ),
        'output_filename': 'build/mobile-landings-get-involved-min.css'
    },
    'badges': {
        'source_filenames': (
            'sumo/less/badges.less',
        ),
        'output_filename': 'build/badges-min.css'
    }
}

PIPELINE_JS = {
    'common': {
        'source_filenames': (
            'sumo/js/i18n.js',
            'underscore/underscore.js',
            'moment/moment.js',
            'jquery/jquery.min.js',
            'jquery/jquery-migrate.js',
            'sumo/js/libs/jquery.cookie.js',
            'sumo/js/libs/jquery.placeholder.js',
            'sumo/js/templates/macros.js',
            'sumo/js/templates/search-results-list.js',
            'sumo/js/templates/search-results.js',
            'nunjucks/browser/nunjucks-slim.js',
            'sumo/js/nunjucks.js',
            'sumo/js/cached_xhr.js',
            'sumo/js/search_utils.js',
            'sumo/js/browserdetect.js',
            'sumo/js/libs/uitour.js',
            'sumo/js/kbox.js',
            'sumo/js/main.js',
            'sumo/js/format.js',
            'modernizr/modernizr.js',
            'sumo/js/geoip-locale.js',
            'mailcheck/src/mailcheck.js',
            'sumo/js/ui.js',
            'sumo/js/analytics.js',
            'sumo/js/surveygizmo.js',
            'sumo/js/instant_search.js',
            'sumo/js/legacy_login_toggle.js',
            'sumo/js/responsive-nav-toggle.js',
            'sumo/js/profile-avatars.js'
        ),
        'output_filename': 'build/common-min.js'
    },
    'common.fx.download': {
        'source_filenames': (
            'sumo/js/show-fx-download.js',
        ),
        'output_filename': 'build/show-fx-download.js'
    },
    'community': {
        'source_filenames': (
            'jquery/jquery.min.js',
            'jquery/jquery-migrate.js',
            'community/js/community.js',
            'community/js/select.js',
        ),
        'output_filename': 'build/community-min.js'
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
            'community/js/community-questions.browserify.js',
        ),
        'output_filename': 'build/community-questions-min.js'
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
            'community/js/community-l10n.browserify.js',
        ),
        'output_filename': 'build/community-l10n-min.js'
    },
    'community.metrics': {
        'source_filenames': (
            'kpi/js/kpi.browserify.js',
        ),
        'output_filename': 'build/kpi.dashboard-min.js'
    },
    'mobile-common': {
        'source_filenames': (
            'sumo/js/templates/mobile-search-results.js',
            'moment/moment.js',
            'sumo/js/i18n.js',
            'underscore/underscore.js',
            'jquery/jquery.min.js',
            'jquery/jquery-migrate.js',
            'modernizr/modernizr.js',
            'nunjucks/browser/nunjucks-slim.js',
            'sumo/js/nunjucks.js',
            'sumo/js/browserdetect.js',
            'sumo/js/cached_xhr.js',
            'sumo/js/search_utils.js',
            'sumo/js/aaq.js',
            'sumo/js/mobile/ui.js',
            'sumo/js/analytics.js',
            'sumo/js/instant_search.js',
            'sumo/js/mobile/instant_search.js',
        ),
        'output_filename': 'build/mobile-common-min.js'
    },
    'ie6-8': {
        'source_filenames': (
            'nwmatcher/src/nwmatcher.js',
            'sumo/js/libs/selectivizr-1.0.2.js',
        ),
        'output_filename': 'build/ie6-8-min.js'
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
        'output_filename': 'build/jqueryui-min.js'
    },
    'questions': {
        'source_filenames': (
            'sumo/js/markup.js',
            'sumo/js/ajaxvote.js',
            'sumo/js/ajaxpreview.js',
            'sumo/js/remote.js',
            'sumo/js/aaq.js',
            'sumo/js/questions.js',
            'sumo/js/libs/jquery.tokeninput.js',
            'sumo/js/tags.filter.js',
            'sumo/js/tags.js',
            'sumo/js/reportabuse.js',
            'sumo/js/questions.metrics.js',
            'sumo/js/libs/jquery.ajaxupload.js',
            'sumo/js/upload.js',
        ),
        'output_filename': 'build/questions-min.js'
    },
    'questions.metrics': {
        'source_filenames': (
            'sumo/js/questions.metrics-dashboard.js',
        ),
        'output_filename': 'build/questions.metrics-min.js'
    },
    'questions.aaq.react': {
        'source_filenames': (
            # This uses the minified version because it is optimized to leave
            # out lots of debug stuff, so it is significantly smaller than
            # just minifying react.js.
            # TODO: Figure out how to include the full sized version in dev,
            # because it produces much nicer error messages.
            'react/react.min.js',
            # 'react/react.js',
            'flux/dist/Flux.js',
            'underscore/underscore.js',

            'questions/js/aaq.browserify.js',

        ),
        'output_filename': 'build/questions.aaq.react-min.js',
    },
    'mobile-questions': {
        'source_filenames': (
            'sumo/js/mobile/questions.js',
            'sumo/js/questions.metrics.js',
        ),
        'output_filename': 'build/mobile-questions-min.js'
    },
    'mobile-aaq': {
        'source_filenames': (
            'sumo/js/aaq.js',
            'sumo/js/mobile/aaq.js',
        ),
        'output_filename': 'build/mobile-aaq-min.js'
    },
    'products': {
        'source_filenames': (
            'sumo/js/compare_versions.js',
            'sumo/js/products.js',
        ),
        'output_filename': 'build/products-min.js'
    },
    'mobile-products': {
        'source_filenames': (
            'sumo/js/templates/mobile-product-search-results.js',
            'nunjucks/browser/nunjucks-slim.js',
            'sumo/js/nunjucks.js',
            'moment/moment.js',
            'sumo/js/cached_xhr.js',
            'sumo/js/search_utils.js',
            'sumo/js/instant_search.js',
            'sumo/js/mobile/products.js',
        ),
        'output_filename': 'build/mobile-products-min.js'
    },
    'search': {
        'source_filenames': (
            'sumo/js/search.js',
        ),
        'output_filename': 'build/search-min.js'
    },
    'forums': {
        'source_filenames': (
            'sumo/js/markup.js',
            'sumo/js/ajaxpreview.js',
            'sumo/js/forums.js',
            'sumo/js/reportabuse.js',
        ),
        'output_filename': 'build/forums-min.js'
    },
    'gallery': {
        'source_filenames': (
            'sumo/js/libs/jquery.ajaxupload.js',
            'sumo/js/gallery.js',
        ),
        'output_filename': 'build/gallery-min.js'
    },
    'wiki': {
        'source_filenames': (
            'sumo/js/markup.js',
            'sumo/js/libs/django/urlify.js',
            'sumo/js/libs/django/prepopulate.js',
            'sumo/js/libs/jquery.lazyload.js',
            'sumo/js/libs/jquery.tokeninput.js',
            'sumo/js/users.autocomplete.js',
            'sumo/js/screencast.js',
            'sumo/js/showfor.js',
            'sumo/js/ajaxvote.js',
            'sumo/js/ajaxpreview.js',
            'sumo/js/wiki.js',
            'sumo/js/tags.js',
            'sumo/js/dashboards.js',
            'sumo/js/editable.js',
            'sumo/js/wiki.metrics.js',
            'sumo/js/templates/wiki-related-doc.js',
            'sumo/js/templates/wiki-search-results.js',
            'sumo/js/wiki_search.js',
        ),
        'output_filename': 'build/wiki-min.js'
    },
    'rickshaw': {
        'source_filenames': (
            'd3/d3.js',
            'sumo/js/libs/d3.layout.min.js',
            'sumo/js/libs/rickshaw.js',
            'sumo/js/rickshaw_utils.js',
        ),
        'output_filename': 'build/rickshaw-min.js'
    },
    'mobile-wiki': {
        'source_filenames': (
            'underscore/underscore.js',
            'sumo/js/libs/jquery.cookie.js',
            'sumo/js/libs/jquery.lazyload.js',
            'sumo/js/browserdetect.js',
            'sumo/js/showfor.js',
            'sumo/js/ajaxform.js',
            'sumo/js/mobile/wiki.js',
            'sumo/js/wiki.metrics.js',
        ),
        'output_filename': 'build/mobile-wiki-min.js'
    },
    'mobile-wiki-minimal': {
        'source_filenames': (
            'sumo/js/i18n.js',
            'underscore/underscore.js',
            'jquery/jquery.min.js',
            'jquery/jquery-migrate.js',
            'modernizr/modernizr.js',
            'sumo/js/browserdetect.js',
            'sumo/js/mobile/ui.js',
            'sumo/js/analytics.js',
            'sumo/js/libs/jquery.cookie.js',
            'sumo/js/libs/jquery.lazyload.js',
            'sumo/js/showfor.js',
            'sumo/js/ajaxform.js',
            'sumo/js/mobile/wiki.js',
            'sumo/js/wiki.metrics.js',
        ),
        'output_filename': 'build/mobile-wiki-minimal-min.js'
    },
    'wiki.history': {
        'source_filenames': (
            'sumo/js/historycharts.js',
        ),
        'output_filename': 'build/wiki.history-min.js'
    },
    'wiki.diff': {
        'source_filenames': (
            'sumo/js/libs/diff_match_patch_uncompressed.js',
            'sumo/js/diff.js',
        ),
        'output_filename': 'build/wiki.diff-min.js'
    },
    'wiki.editor': {
        'source_filenames': (
            'codemirror/lib/codemirror.js',
            'codemirror/addon/mode/simple.js',
            'codemirror/addon/hint/show-hint.js',
            'sumo/js/codemirror.sumo-hint.js',
            'sumo/js/codemirror.sumo-mode.js',
        ),
        'output_filename': 'build/wiki.editor-min.js'
    },
    'wiki.dashboard': {
        'source_filenames': (
            'sumo/js/wiki.dashboard.js',
        ),
        'output_filename': 'build/wiki.dashboard-min.js'
    },
    'customercare': {
        'source_filenames': (
            'sumo/js/libs/jquery.cookie.js',
            'sumo/js/libs/jquery.bullseye-1.0.min.js',
            'sumo/js/libs/twitter-text.js',
            'sumo/js/customercare.js',
            'sumo/js/users.js',
        ),
        'output_filename': 'build/customercare-min.js'
    },
    'users': {
        'source_filenames': (
            'sumo/js/users.js',
            'sumo/js/reportabuse.js',
        ),
        'output_filename': 'build/users-min.js'
    },
    'messages': {
        'source_filenames': (
            'sumo/js/markup.js',
            'sumo/js/libs/jquery.autoresize.js',
            'sumo/js/libs/jquery.tokeninput.js',
            'sumo/js/users.autocomplete.js',
            'sumo/js/ajaxpreview.js',
            'sumo/js/messages.js',
        ),
        'output_filename': 'build/messages-min.js'
    },
    'mobile-messages': {
        'source_filenames': (
            'sumo/js/libs/jquery.tokeninput.js',
            'sumo/js/users.autocomplete.js',
        ),
        'output_filename': 'build/mobile-messages-min.js'
    },
    'groups': {
        'source_filenames': (
            'sumo/js/libs/jquery.tokeninput.js',
            'sumo/js/users.autocomplete.js',
            'sumo/js/markup.js',
            'sumo/js/groups.js',
            'sumo/js/editable.js',
        ),
        'output_filename': 'build/groups-min.js'
    },
    'kpi.dashboard': {
        'source_filenames': (
            'd3/d3.js',
            'kpi/js/kpi.browserify.js',
        ),
        'output_filename': 'build/kpi.dashboard-min.js'
    },
    'experiment_fxa_cta_topbar': {
        'source_filenames': (
            'sumo/js/libs/mozilla-dnt-helper.js',
            'sumo/js/libs/mozilla-cookie-helper.js',
            'sumo/js/libs/mozilla-traffic-cop.js',
            'sumo/js/experiment-fxa-cta-topbar.js',
        ),
        'output_filename': 'build/experiment-fxa-cta-topbar-min.js'
    },
    'gtm-snippet': {
        'source_filenames': (
            'sumo/js/dnt-helper.js',
            'sumo/js/gtm-snippet.js',
        ),
        'output_filename': 'build/gtm-snippet-min.js'
    }
}
