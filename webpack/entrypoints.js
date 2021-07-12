module.exports = {
  screen: ["sumo/scss/screen.scss"],
  common: [
    "sumo/js/i18n.js",
    "underscore/underscore.js",
    "moment/moment.js",
    "jquery",
    "sumo/js/libs/jquery.cookie.js",
    "sumo/js/libs/jquery.placeholder.js",
    "sumo/js/templates/macros.js",
    "sumo/js/templates/search-results-list.js",
    "sumo/js/templates/search-results.js",
    "nunjucks/browser/nunjucks-slim.js",
    "sumo/js/nunjucks.js",
    "sumo/js/cached_xhr.js",
    "sumo/js/search_utils.es6",
    "sumo/js/browserdetect.js",
    "sumo/js/libs/uitour.js",
    "sumo/js/kbox.js",
    "sumo/js/main.js",
    "sumo/js/libs/modernizr-custom-build.js",
    "sumo/js/geoip-locale.js",
    "sumo/js/ui.js",
    "sumo/js/analytics.js",
    "sumo/js/instant_search.es6",
    "sumo/js/responsive-nav-toggle.js",
    "sumo/js/profile-avatars.js",
    "./webpack/protocol-compat.js",
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
    "sumo/js/protocol-nav.es6",
    "sumo/js/protocol-details-init.js",
    "sumo/js/protocol-modal-init.es6",
    "sumo/js/protocol-notification-init.js",
    "sumo/js/protocol-language-switcher-init.js",
    "sumo/js/sumo-tabs.es6",
    "sumo/js/sumo-close-this.es6",
  ],
  "common.fx.download": [
    "sumo/js/show-fx-download.js",
  ],
  community: [
    "jquery",
    "community/js/community.js",
    "community/js/select.js",
  ],
  "community.metrics": [
    "kpi/js/kpi.browserify.js",
  ],
  jqueryui: [
    "sumo/js/jquery-ui-custom.js",
  ],
  questions: [
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
  ],
  "questions.metrics": [
    "sumo/js/questions.metrics-dashboard.js",
  ],
  products: [
    "sumo/js/compare_versions.js",
    "sumo/js/products.js",
  ],
  search: [
    "sumo/js/search.js",
  ],
  forums: [
    "sumo/js/markup.js",
    "sumo/js/ajaxpreview.js",
    "sumo/js/forums.js",
    "sumo/js/reportabuse.js",
  ],
  gallery: [
    "sumo/js/libs/jquery.ajaxupload.js",
    "sumo/js/gallery.js",
  ],
  wiki: [
    "sumo/js/markup.js",
    "sumo/js/libs/django/urlify.js",
    "sumo/js/libs/django/prepopulate.js",
    "sumo/js/libs/jquery.lazyload.js",
    "sumo/js/libs/jquery.tokeninput.js",
    "sumo/js/users.autocomplete.js",
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
  ],
  rickshaw: [
    "d3/d3.js",
    "sumo/js/libs/d3.layout.min.js",
    "sumo/js/libs/rickshaw.js",
    "sumo/js/rickshaw_utils.js",
  ],
  "wiki.history": [
    "sumo/js/historycharts.js",
  ],
  "wiki.diff": [
    "sumo/js/libs/diff_match_patch_uncompressed.js",
    "sumo/js/diff.js",
  ],
  "wiki.editor": [
    "codemirror/lib/codemirror.js",
    "codemirror/addon/mode/simple.js",
    "codemirror/addon/hint/show-hint.js",
    "sumo/js/codemirror.sumo-hint.js",
    "sumo/js/codemirror.sumo-mode.js",
  ],
  "wiki.dashboard": [
    "sumo/js/wiki.dashboard.js",
  ],
  users: [
    "sumo/js/users.js",
    "sumo/js/reportabuse.js",
  ],
  messages: [
    "sumo/js/markup.js",
    "sumo/js/libs/jquery.autoresize.js",
    "sumo/js/libs/jquery.tokeninput.js",
    "sumo/js/users.autocomplete.js",
    "sumo/js/ajaxpreview.js",
    "sumo/js/messages.js",
  ],
  groups: [
    "sumo/js/libs/jquery.tokeninput.js",
    "sumo/js/users.autocomplete.js",
    "sumo/js/markup.js",
    "sumo/js/groups.js",
    "sumo/js/editable.js",
  ],
  "kpi.dashboard": [
    "d3/d3.js",
    "kpi/js/kpi.browserify.js",
  ],
  "gtm-snippet": [
    "sumo/js/dnt-helper.js",
    "sumo/js/gtm-snippet.js",
  ],
}
