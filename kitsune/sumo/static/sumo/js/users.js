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
    $('.deactivate').on("submit", function() {
      return confirm(CONFIRM_TEXT);
    });
  }

  function handleAccountDeletion() {
    // Handle the delete account button click 
    $('#delete-profile-button').on('click', function(e) {
      e.preventDefault();
      
      var $form = $(this).closest('form');
      
      // Close modals - keep both systems for compatibility
      if (typeof Mzp !== 'undefined' && Mzp.Modal) {
        Mzp.Modal.closeModal();
      }
      
      if ($.kbox) {
        $.kbox.close();
      }
      
      // Directly submit the form after a small delay
      // This ensures the modal closing completes before submission
      setTimeout(function() {
        $form[0].submit();
      }, 50);
    });
  }

  $(function() {
    makeEmailsClickable();
    confirmUserDeactivation();
    handleAccountDeletion();
  });
})(jQuery);
