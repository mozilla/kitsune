/* globals gettext:false, trackEvent:false, jQuery */
/*
 * users.js
 * Make public emails clickable.
 */

(function ($) {
  function makeEmailsClickable() {
    // bail if no emails on page
    var $emails = $('.email');
    if ($emails.length === 0) {
      return false;
    }
    $emails.each(function () {
      var email_val = $(this).text();
      var $a = $('<a/>').attr('href', 'mailto:' + email_val)
      .html(email_val);
      $(this).html($a);
    });
  }

  var CONFIRM_TEXT = gettext('WARNING! Are you sure you want to deactivate this user? This cannot be undone!');
  function confirmUserDeactivation() {
    $('.deactivate').submit(function() {
      return confirm(CONFIRM_TEXT); // eslint-disable-line
    });
  }

  $(function() {
    makeEmailsClickable();
    confirmUserDeactivation();

    if ($('body').is('.register') && window.location.search.indexOf('reg=aaq') > -1) {
      trackEvent('Ask A Question Flow', 'step 3 confirmed page');
    }
  });
})(jQuery);
