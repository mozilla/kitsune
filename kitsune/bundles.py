# Bundles for JS/CSS Minification

PIPELINE_JS = {
    "common": {
        "source_filenames": (
            "sumo/js/i18n.js",
            "underscore/underscore.js",
            "moment/moment.js",
            "jquery/dist/jquery.min.js",
            "jquery/jquery-migrate.js",
            "sumo/js/libs/jquery.cookie.js",
            "sumo/js/libs/jquery.placeholder.js",
            "sumo/js/templates/macros.js",
            "sumo/js/templates/search-results-list.js",
            "sumo/js/templates/search-results.js",
            "nunjucks/browser/nunjucks-slim.js",
            "sumo/js/nunjucks.js",
            "sumo/js/cached_xhr.js",
            "sumo/js/search_utils.js",
            "sumo/js/browserdetect.js",
            "sumo/js/libs/uitour.js",
            "sumo/js/kbox.js",
            "sumo/js/main.js",
            "sumo/js/format.js",
            "sumo/js/libs/modernizr-custom-build.js",
            "sumo/js/geoip-locale.js",
            "mailcheck/src/mailcheck.js",
            "sumo/js/ui.js",
            "sumo/js/analytics.js",
            "sumo/js/surveygizmo.js",
            "sumo/js/instant_search.js",
            "sumo/js/responsive-nav-toggle.js",
            "sumo/js/profile-avatars.js",
            "protocol/js/protocol-base.js",
            "protocol/js/protocol-utils.js",
            "protocol/js/protocol-supports.js",
            "protocol/js/protocol-details.js",
            "protocol/js/protocol-footer.js",
            "protocol/js/protocol-menu.js",
            "protocol/js/protocol-modal.js",
            "protocol/js/protocol-navigation.js",
            "protocol/js/protocol-newsletter.js",
            "protocol/js/protocol-notification-bar.js",
            "protocol/js/protocol-lang-switcher.js",
            "sumo/js/protocol-nav.js",
            "sumo/js/protocol-details-init.js",
            "sumo/js/protocol-modal-init.js",
            "sumo/js/protocol-notification-init.js",
            "sumo/js/protocol-language-switcher-init.js",
            "sumo/js/sumo-tabs.js",
            "sumo/js/sumo-close-this.js",
        ),
        "output_filename": "build/common-min.js",
    },
    "common.fx.download": {
        "source_filenames": ("sumo/js/show-fx-download.js",),
        "output_filename": "build/show-fx-download.js",
    },
    "community": {
        "source_filenames": (
            "jquery/jquery.min.js",
            "jquery/jquery-migrate.js",
            "community/js/community.js",
            "community/js/select.js",
        ),
        "output_filename": "build/community-min.js",
    },
    "community-new-questions": {
        "source_filenames": (
            # This uses the minified version because it is optimized to leave
            # out lots of debug stuff, so it is significantly smaller than
            # just minifying react.js.
            # TODO: Figure out how to include the full sized version in dev,
            # because it produces much nicer error messages.
            "react/react.min.js",
            # 'react/react.js',
            "pikaday/pikaday.js",
            "community/js/community-questions.browserify.js",
        ),
        "output_filename": "build/community-questions-min.js",
    },
    "community-new-l10n": {
        "source_filenames": (
            # This uses the minified version because it is optimized to leave
            # out lots of debug stuff, so it is significantly smaller than
            # just minifying react.js.
            # TODO: Figure out how to include the full sized version in dev,
            # because it produces much nicer error messages.
            "react/react.min.js",
            # 'react/react.js',
            "pikaday/pikaday.js",
            "community/js/community-l10n.browserify.js",
        ),
        "output_filename": "build/community-l10n-min.js",
    },
    "community.metrics": {
        "source_filenames": ("kpi/js/kpi.browserify.js",),
        "output_filename": "build/kpi.dashboard-min.js",
    },
    "jqueryui": {
        "source_filenames": ("sumo/js/jquery-ui-custom.js",),
        "output_filename": "build/jqueryui-min.js",
    },
    "questions": {
        "source_filenames": (
            "sumo/js/markup.js",
            "sumo/js/ajaxvote.js",
            "sumo/js/ajaxpreview.js",
            "sumo/js/remote.js",
            "sumo/js/aaq.js",
            "sumo/js/questions.js",
            "sumo/js/libs/jquery.tokeninput.js",
            "sumo/js/tags.filter.js",
            "sumo/js/tags.js",
            "sumo/js/reportabuse.js",
            "sumo/js/questions.metrics.js",
            "sumo/js/libs/jquery.ajaxupload.js",
            "sumo/js/upload.js",
        ),
        "output_filename": "build/questions-min.js",
    },
    "questions.metrics": {
        "source_filenames": ("sumo/js/questions.metrics-dashboard.js",),
        "output_filename": "build/questions.metrics-min.js",
    },
    "products": {
        "source_filenames": ("sumo/js/compare_versions.js", "sumo/js/products.js",),
        "output_filename": "build/products-min.js",
    },
    "search": {
        "source_filenames": ("sumo/js/search.js",),
        "output_filename": "build/search-min.js",
    },
    "forums": {
        "source_filenames": (
            "sumo/js/markup.js",
            "sumo/js/ajaxpreview.js",
            "sumo/js/forums.js",
            "sumo/js/reportabuse.js",
        ),
        "output_filename": "build/forums-min.js",
    },
    "gallery": {
        "source_filenames": ("sumo/js/libs/jquery.ajaxupload.js", "sumo/js/gallery.js",),
        "output_filename": "build/gallery-min.js",
    },
    "wiki": {
        "source_filenames": (
            "sumo/js/markup.js",
            "sumo/js/libs/django/urlify.js",
            "sumo/js/libs/django/prepopulate.js",
            "sumo/js/libs/jquery.lazyload.js",
            "sumo/js/libs/jquery.tokeninput.js",
            "sumo/js/users.autocomplete.js",
            "sumo/js/screencast.js",
            "sumo/js/showfor.js",
            "sumo/js/ajaxvote.js",
            "sumo/js/ajaxpreview.js",
            "sumo/js/wiki.js",
            "sumo/js/tags.js",
            "sumo/js/dashboards.js",
            "sumo/js/editable.js",
            "sumo/js/wiki.metrics.js",
            "sumo/js/templates/wiki-related-doc.js",
            "sumo/js/templates/wiki-search-results.js",
            "sumo/js/wiki_search.js",
        ),
        "output_filename": "build/wiki-min.js",
    },
    "rickshaw": {
        "source_filenames": (
            "d3/d3.js",
            "sumo/js/libs/d3.layout.min.js",
            "sumo/js/libs/rickshaw.js",
            "sumo/js/rickshaw_utils.js",
        ),
        "output_filename": "build/rickshaw-min.js",
    },
    "wiki.history": {
        "source_filenames": ("sumo/js/historycharts.js",),
        "output_filename": "build/wiki.history-min.js",
    },
    "wiki.diff": {
        "source_filenames": ("sumo/js/libs/diff_match_patch_uncompressed.js", "sumo/js/diff.js",),
        "output_filename": "build/wiki.diff-min.js",
    },
    "wiki.editor": {
        "source_filenames": (
            "codemirror/lib/codemirror.js",
            "codemirror/addon/mode/simple.js",
            "codemirror/addon/hint/show-hint.js",
            "sumo/js/codemirror.sumo-hint.js",
            "sumo/js/codemirror.sumo-mode.js",
        ),
        "output_filename": "build/wiki.editor-min.js",
    },
    "wiki.dashboard": {
        "source_filenames": ("sumo/js/wiki.dashboard.js",),
        "output_filename": "build/wiki.dashboard-min.js",
    },
    "customercare": {
        "source_filenames": (
            "sumo/js/libs/jquery.cookie.js",
            "sumo/js/libs/jquery.bullseye-1.0.min.js",
            "sumo/js/libs/twitter-text.js",
            "sumo/js/customercare.js",
            "sumo/js/users.js",
        ),
        "output_filename": "build/customercare-min.js",
    },
    "users": {
        "source_filenames": ("sumo/js/users.js", "sumo/js/reportabuse.js",),
        "output_filename": "build/users-min.js",
    },
    "messages": {
        "source_filenames": (
            "sumo/js/markup.js",
            "sumo/js/libs/jquery.autoresize.js",
            "sumo/js/libs/jquery.tokeninput.js",
            "sumo/js/users.autocomplete.js",
            "sumo/js/ajaxpreview.js",
            "sumo/js/messages.js",
        ),
        "output_filename": "build/messages-min.js",
    },
    "groups": {
        "source_filenames": (
            "sumo/js/libs/jquery.tokeninput.js",
            "sumo/js/users.autocomplete.js",
            "sumo/js/markup.js",
            "sumo/js/groups.js",
            "sumo/js/editable.js",
        ),
        "output_filename": "build/groups-min.js",
    },
    "kpi.dashboard": {
        "source_filenames": ("d3/d3.js", "kpi/js/kpi.browserify.js",),
        "output_filename": "build/kpi.dashboard-min.js",
    },
    "experiment_fxa_cta_topbar": {
        "source_filenames": (
            "sumo/js/libs/mozilla-dnt-helper.js",
            "sumo/js/libs/mozilla-cookie-helper.js",
            "sumo/js/libs/mozilla-traffic-cop.js",
            "sumo/js/experiment-fxa-cta-topbar.js",
        ),
        "output_filename": "build/experiment-fxa-cta-topbar-min.js",
    },
    "gtm-snippet": {
        "source_filenames": ("sumo/js/dnt-helper.js", "sumo/js/gtm-snippet.js",),
        "output_filename": "build/gtm-snippet-min.js",
    },
}
