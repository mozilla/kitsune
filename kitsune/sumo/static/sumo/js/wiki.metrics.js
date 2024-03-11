// Collect wiki metrics.
import trackEvent from "sumo/js/analytics";

// The "DOMContentLoaded" event is guaranteed not to have been
// called by the time the following code is run, because it always
// waits until all deferred scripts have been loaded, and the code
// in this file is always bundled into a script that is deferred.
document.addEventListener("DOMContentLoaded", () => {
  const body = document.querySelector("body.document");
  if (body) {
    const html = document.querySelector("html");
    const locale = html.getAttribute("lang");
    const gaTopics = html.dataset.gaTopics;
    const gaProducts = html.dataset.gaProducts;
    const defaultSlug = body.dataset.defaultSlug;
    const versionSelect = document.querySelector("#showfor-panel select.version");
    const platformSelect = document.querySelector("#showfor-panel select.platform");

    // Track votes in GA.
    document.addEventListener("vote", (event) => {
      if (('helpful' in event.detail) || ('not-helpful' in event.detail)) {
        trackEvent("article_vote", {
          "locale": locale,
          "default_slug": defaultSlug,
          "vote": ("helpful" in event.detail) ? "helpful": "not-helpful",
          "products": gaProducts,
          "topics": gaTopics
        });
      }
    });

    // Track showfor changes in GA.
    if (versionSelect) {
      versionSelect.addEventListener("change", function(event) {
        trackEvent("showfor_version_change", {
          "locale": locale,
          "value": this.value,
          "default_slug": defaultSlug,
          "products": gaProducts,
          "topics": gaTopics
        });
      });
    }
    if (platformSelect) {
      platformSelect.addEventListener("change", function(event) {
        trackEvent("showfor_platform_change", {
          "locale": locale,
          "value": this.value,
          "default_slug": defaultSlug,
          "products": gaProducts,
          "topics": gaTopics
        });
      });
    }

    // Fire a GA event after 10 seconds to track an engaged article "read".
    setTimeout(function() {
      trackEvent('article_read', {
        "locale": locale,
        "default_slug": defaultSlug,
        "products": gaProducts,
        "topics": gaTopics
      });
    }, 10000);
  }
});
