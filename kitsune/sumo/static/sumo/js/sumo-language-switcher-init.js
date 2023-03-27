/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

(function() {
  'use strict';

  var LangSwitcher = {};

  /**
   * Redirect page to destination URL if valid
   * @param {String} destination
   */
  LangSwitcher.doRedirect = function(destination) {
      if (destination) {
          window.location.href = destination;
      }
  };

  /**
   * Initialize footer lang switcher.
   * @param {function} Custom callback for analytics.
   */
  LangSwitcher.init = function(callback) {
      var language = document.querySelectorAll('.sumo-js-language-switcher-select');

      for (var i = 0; i < language.length; i++) {
          language[i].setAttribute('data-previous-url', language[i].value);

          language[i].addEventListener('change', function(e) {
              var newURL = e.target.value;
              var previousURL = e.target.getAttribute('data-previous-url');

              // support custom callback for page analytics.
              if (typeof callback === 'function') {
                  callback(previousURL, newURL);
              }

              LangSwitcher.doRedirect(newURL);
          }, false);
      }

  };

  // a custom callback can be passed to the lang switcher for analytics purposes.
  LangSwitcher.init(function(previousURL, newURL) {
    console.log('Previous url: ', previousURL);
    console.log('New url: ', newURL);
  })

})();
