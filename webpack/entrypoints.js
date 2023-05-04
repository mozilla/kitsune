const entrypoints = {
  screen: ["sumo/scss/screen.scss"],
  common: [
    "sumo/js/i18n.js",
    "sumo/js/kbox.js",
    "sumo/js/main.js",
    "sumo/js/geoip-locale.js",
    "sumo/js/ui.js",
    "sumo/js/analytics.js",
    "sumo/js/instant_search.js",
    "sumo/js/responsive-nav-toggle.js",
    "sumo/js/profile-avatars.js",
    "sumo/js/protocol.js",
    "sumo/js/protocol-nav.js",
    "sumo/js/protocol-details-init.js",
    "sumo/js/protocol-modal-init.js",
    "sumo/js/protocol-notification-init.js",
    "sumo/js/protocol-language-switcher-init.js",
    "sumo/js/sumo-tabs.js",
    "sumo/js/sumo-close-this.js",
    // TODO: remove this - just for testing
    "sumo/js/form-wizard.js",
  ],
  "common.fx.download": [
    "sumo/js/show-fx-download.js",
  ],
  community: [
    "community/js/community.js",
    "community/js/select.js",
  ],
  "community.metrics": [
    "kpi/js/kpi.browserify.js",
  ],
  document: [
    "sumo/js/document.js",
    "sumo/js/wiki.metrics.js",
  ],
  "switching-devices": [
    "sumo/js/device-migration-wizard.js",
  ],
  revision: [
    "sumo/js/revision.js",
  ],
  questions: [
    "sumo/js/questions.js",
    "sumo/js/tags.filter.js",
    "sumo/js/tags.js",
    "sumo/js/reportabuse.js",
    "sumo/js/questions.metrics.js",
    "sumo/js/upload.js",
  ],
  "questions.metrics": [
    "sumo/js/questions.metrics-dashboard.js",
  ],
  "questions.geo": [
    "sumo/js/location.js",
  ],
  products: [
    "sumo/js/products.js",
  ],
  search: [
    "sumo/js/search.js",
  ],
  forums: [
    "sumo/js/forums.js",
    "sumo/js/reportabuse.js",
  ],
  gallery: [
    "sumo/js/gallery.js",
  ],
  wiki: [
    "sumo/js/users.autocomplete.js",
    "sumo/js/wiki.js",
    "sumo/js/dashboards.js",
    "sumo/js/editable.js",
    "sumo/js/wiki_search.js",
  ],
  "wiki.history": [
    "sumo/js/historycharts.js",
  ],
  "wiki.diff": [
    "sumo/js/diff.js",
  ],
  "wiki.editor": [
    "sumo/js/wiki.editor.js",
  ],
  "wiki.dashboard": [
    "sumo/js/wiki.dashboard.js",
  ],
  users: [
    "sumo/js/users.js",
    "sumo/js/reportabuse.js",
  ],
  messages: [
    "sumo/js/users.autocomplete.js",
    "sumo/js/messages.js",
  ],
  groups: [
    "sumo/js/users.autocomplete.js",
    "sumo/js/groups.js",
    "sumo/js/editable.js",
  ],
  "kpi.dashboard": [
    "kpi/js/kpi.browserify.js",
  ],
  "gtm-snippet": [
    "sumo/js/gtm-snippet.js",
  ],
  contribute: [
    "./svelte/contribute",
  ]
}

for (let key in entrypoints) {
  if (key !== "common") {
    // mark all entrypoints as dependent on "common" (other than itself)
    // this ensures we don't duplicate chunks across "common" and other bundles
    // and ensures "common" contains the only webpack runtime
    entrypoints[key] = {
      import: entrypoints[key],
      dependOn: "common",
    }
  }
}

module.exports = entrypoints
