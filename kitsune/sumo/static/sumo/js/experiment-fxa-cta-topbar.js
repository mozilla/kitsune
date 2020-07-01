(function (Mozilla) {
  "use strict";

  // callback for UITour conditional
  var rogerThat = function (sync) {
    // only run if not syncing
    var notSyncing = !sync.detail.data.setup;

    if (notSyncing) {
      var showPromotion = function (variation) {
        document.addEventListener("DOMContentLoaded", function () {
          var promotions = document.getElementById("promotions");
          var showContent = promotions.querySelector(
            'a[data-variation="' + variation + '"]'
          );
          var links = promotions.getElementsByTagName("a");

          for (var i = 0; i < links.length; i++) {
            links[i].href = links[i].href + "&utm_term=" + variation;
          }

          showContent.className = showContent.className.replace("hidden", "");
          promotions.className = promotions.className.replace("hidden", "");

          // fire a non-interactive analytics event indicating this variation appeared on the screen
          if (window.gtag) {
            window.gtag("event", "view", {
              event_category: "experiment-fxa-cta-topbar",
              event_label: variation,
              nonInteraction: true,
            });
          }
        });
      };

      var laverneHooks = new Mozilla.TrafficCop({
        id: "experiment-fxa-cta-topbar",
        customCallback: showPromotion,
        variations: {
          a: 34,
          b: 33,
          c: 33,
        },
      });

      laverneHooks.init();
    }
  };

  // only run on Firefox 40+
  var isRecentFirefox = (function () {
    var matches = /Firefox\/(\d+(?:\.\d+){1,2})/.exec(navigator.userAgent);
    return matches && Number(matches[1]) >= 40;
  })();

  if (isRecentFirefox) {
    var event = new CustomEvent("mozUITour", {
      bubbles: true,
      detail: {
        action: "getConfiguration",
        data: { configuration: "sync" },
      },
    });

    document.addEventListener("mozUITourResponse", rogerThat, { once: true });
    document.dispatchEvent(event);
  }
})(window.Mozilla);
