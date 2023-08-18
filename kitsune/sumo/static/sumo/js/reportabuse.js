/*
* Report abuse UI.
*/

(function($) {
  'use strict';

  $(function() {
    $('#report-abuse input[type=radio][name=reason]').on('change', function(ev) {
      $(this).closest('form').siblings('.message').text('');
    });

    $('#report-abuse [type=submit]').on('click', function(ev) {
      ev.preventDefault();
      let $form = $(this).closest('form');
      let reason = $form.find('input[type=radio][name=reason]:checked').val();

      if (!reason) {
        $form.siblings('.message').text(gettext('Please select a reason.'));
        return;
      }

      if (reason === 'other' && !$form.find('textarea[name=other]').val().trim()) {
        $form.siblings('.message').text(gettext('Please provide more detail.'));
        return;
      }

      $.ajax({
        url: $form.attr('action'),
        type: 'POST',
        data: $form.serialize(),
        dataType: 'json',

        success: function(data) {
          $form.siblings('.message').text(data.message);
          $form.slideUp();
        },
        error: function(error) {
          $form.siblings('.message')
          .text(gettext('There was an error. Please try again in a moment.'));
          $form.slideUp();
        }
      });
    });
  });

})(jQuery);
