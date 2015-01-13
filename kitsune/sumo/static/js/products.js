(function($, BD) {
    "use strict";

    $(function() {
      var latestVersion = $('.download-firefox .download-button').data('latest-version');

      if ((BD.version >= latestVersion) && (BD.browser == 'fx')) {
        $('.refresh-firefox').show();
        $('.download-firefox').hide();
      }
    });
})(jQuery, BrowserDetect);
