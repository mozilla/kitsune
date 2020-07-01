/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

(function (w) {
  "use strict";

  var GTM_CONTAINER_ID = document
    .getElementsByTagName("html")[0]
    .getAttribute("data-gtm-container-id");

  var matches;
  var product;

  w.dataLayer = w.dataLayer || [];

  w.gtag = function () {
    w.dataLayer.push(arguments);
  };
  // If doNotTrack is not enabled, it is ok to add GTM
  // @see https://bugzilla.mozilla.org/show_bug.cgi?id=1217896 for more details
  if (typeof _dntEnabled === "function" && !_dntEnabled() && GTM_CONTAINER_ID) {
    (function (w, d, s, l, i, j, f, dl, k, q) {
      w[l] = w[l] || [];
      w[l].push({ "gtm.start": new Date().getTime(), event: "gtm.js" });
      f = d.getElementsByTagName(s)[0];
      k = i.length;
      q = "//www.googletagmanager.com/gtag/js?id=@&l=" + (l || "dataLayer");
      while (k--) {
        j = d.createElement(s);
        j.async = !0;
        j.src = q.replace("@", i[k]);
        f.parentNode.insertBefore(j, f);
      }
    })(window, document, "script", "dataLayer", [GTM_CONTAINER_ID]);

    w.gtag("js", new Date());

    // check for first string after '/products/' and before the next '/'
    matches = w.location.href.match(/.*?\/products\/([\w-]*)\/?/);

    // product should be first match or null
    product = matches && matches.length > 0 ? matches[1] : null;

    w.gtag("config", GTM_CONTAINER_ID, {
      dimension1: product,
    });
  }
})(window);
