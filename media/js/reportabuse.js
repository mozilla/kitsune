/*jshint*/
/*global KBox, k, gettext, _ */
/*
 * Report abuse UI.
 */

(function($) {

"use strict";

$(document).ready(function() {
  $('#report-abuse > a').on('click', function() {
    $(this).siblings('.popup').fadeToggle(300);
  });

  $('#report-abuse .btn[type="cancel"], #report-abuse .kbox-close').on('click', function(ev) {
    $(this).closest('.popup').fadeToggle(300);
  });

  $('#report-abuse .btn[type="submit"]').on('click', function(ev) {
    ev.preventDefault();
    var $this = $(this);
    var $form = $this.parent();

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
