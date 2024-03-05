import trackEvent from "sumo/js/analytics";

// The "DOMContentLoaded" event is guaranteed not to have been
// called by the time the following code is run, because it always
// waits until all deferred scripts have been loaded, and the code
// in this file is always bundled into a script that is deferred.
document.addEventListener("DOMContentLoaded", () => {
  const locale = document.querySelector("html").getAttribute("lang");

  // On page load, after confirming that we're on the search
  // page, send a "search" event if there's a search term.
  if (window.location.pathname === `/${locale}/search/`) {
    const params = new URL(window.location.href).searchParams;
    const searchTerm = params.get("q");
    if (searchTerm) {
      let contentFilter = "";
      let productFilter = params.get("product") || "";

      switch (params.get("w")) {
        case "1":
          contentFilter = "wiki";
          break;
        case "2":
          contentFilter = "aaq";
          break;
        default:
          contentFilter = "all-results";
      }

      trackEvent("search", {
        "search_term": searchTerm,
        "search_product_filter": productFilter,
        "search_content_filter": contentFilter
      });
    }
  }
});
