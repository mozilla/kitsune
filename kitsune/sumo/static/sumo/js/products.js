import UITour from "./libs/uitour";
import compareVersions from "./compare_versions";

(function($, BD) {
  'use strict';

  $(function() {
    var latestVersion = $('.download-firefox .download-button').data('latest-version');

    UITour.getConfiguration('appinfo', function(info) {
      if (compareVersions(info.version, latestVersion) === 0) {
        $('.refresh-firefox').show();
        $('.download-firefox').hide();
      }
    });
  });
})(jQuery, BrowserDetect);
