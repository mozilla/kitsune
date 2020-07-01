/* global gettext:false, _:false, jQuery:false */
/*
 * Report abuse UI.
 */

(function ($) {
  "use strict";

  $(document).ready(function () {
    $('#report-abuse [type="submit"]').on("click", function (ev) {
      ev.preventDefault();
      var $this = $(this);
      var $form = $this.closest("form");

      $.ajax({
        url: $form.attr("action"),
        type: "POST",
        data: $form.serialize(),
        dataType: "json",

        success: function (data) {
          $form.siblings(".message").text(data.message);
          $form.slideUp();
        },
        error: function (error) {
          $form
            .siblings(".message")
            .text(gettext("There was an error. Please try again in a moment."));
          $form.slideUp();
        },
      });
    });
  });
})(jQuery);
