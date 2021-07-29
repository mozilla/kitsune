import UITour from "./libs/uitour";

(function($, BD) {
  'use strict';

  $(function() {
    var latestVersion = $('.download-firefox .download-button').data('latest-version');

    UITour.getConfiguration('appinfo', function(info) {
      if (window.k.compareVersions(info.version, latestVersion) === 0) {
        $('.refresh-firefox').show();
        $('.download-firefox').hide();
      }
    });
  });
})(jQuery, BrowserDetect);
