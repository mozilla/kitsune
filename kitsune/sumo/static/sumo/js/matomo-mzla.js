/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import dntEnabled from "@mozmeao/dnt-helper";

(function (w, d) {
  'use strict';

  let html = d.getElementsByTagName('html')[0];
  let siteId = html.getAttribute('data-matomo-site-id');
  let trackerHost = html.getAttribute('data-matomo-tracker-host');
  let cdnHost = html.getAttribute('data-matomo-cdn-host');

  // Block Matomo if GPC or DNT is enabled, mirroring the GA snippet.
  // GPC is the modern replacement for DNT (Firefox removed DNT in v135, Feb 2025).
  // @see https://globalprivacycontrol.org/
  let trackingBlocked = navigator.globalPrivacyControl ||
                        (typeof dntEnabled === 'function' && dntEnabled());

  if (!trackingBlocked && siteId && trackerHost && cdnHost) {
    let _paq = w._paq = w._paq || [];
    _paq.push(['trackPageView']);
    _paq.push(['enableLinkTracking']);
    let u = 'https://' + trackerHost + '/';
    _paq.push(['setTrackerUrl', u + 'matomo.php']);
    _paq.push(['setSiteId', siteId]);
    let g = d.createElement('script');
    let s = d.getElementsByTagName('script')[0];
    g.async = true;
    g.src = 'https://' + cdnHost + '/' + trackerHost + '/matomo.js';
    s.parentNode.insertBefore(g, s);
  }
})(window, document);
