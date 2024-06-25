/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

import dntEnabled from "./libs/dnt-helper";

(function(w) {
  'use strict';

  let html = document.getElementsByTagName('html')[0];
  let GTM_CONTAINER_ID = html.getAttribute('data-gtm-container-id');

  w.dataLayer = w.dataLayer || [];

  w.gtag = function() {
    w.dataLayer.push(arguments)
  }
  // If doNotTrack is not enabled, it is ok to add GTM
  // @see https://bugzilla.mozilla.org/show_bug.cgi?id=1217896 for more details
  if (typeof dntEnabled === 'function' && !dntEnabled() && GTM_CONTAINER_ID) {
    (function(w,d,s,l,i,j,f,dl,k,q){
      w[l]=w[l]||[];w[l].push({'gtm.start': new Date().getTime(),event:'gtm.js'});f=d.getElementsByTagName(s)[0];
      k=i.length;q='//www.googletagmanager.com/gtag/js?id=@&l='+(l||'dataLayer');
      while (k--) {j=d.createElement(s);j.async=!0;j.src=q.replace('@',i[k]);f.parentNode.insertBefore(j,f);}
    }(window,document,'script','dataLayer',[GTM_CONTAINER_ID]));

    w.gtag('js', new Date());

    let configParameters = {};
    if (html.getAttribute("lang")) {
      configParameters.locale = html.getAttribute("lang");
    }
    if (html.dataset.gaTopics) {
      configParameters.topics = html.dataset.gaTopics;
    }
    if (html.dataset.gaProducts) {
      configParameters.products = html.dataset.gaProducts;
    }
    if (html.dataset.gaContentGroup) {
      configParameters.content_group = html.dataset.gaContentGroup;
    }
    if (html.dataset.gaDefaultSlug) {
      configParameters.default_slug = html.dataset.gaDefaultSlug;
    }
    if (html.dataset.gaArticleLocale) {
      configParameters.article_locale = html.dataset.gaArticleLocale;
    }

    w.gtag('config', GTM_CONTAINER_ID, configParameters);
  }
})(window);
