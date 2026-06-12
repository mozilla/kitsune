import "jquery-ui/ui/widgets/datepicker";
import { getQueryParamsAsDict } from "sumo/js/main";

/*
 * kb dashboard chart
 */

(function($) {

  'use strict';

  $(function() {
    if ($('body').is('.contributor-dashboard')) {
      // Add click events to to the date tabs
      $('.tabs--link').on('click', function() {
        // Clear active class from all tabs--link
        $('.tabs--link').removeClass('is-active');
        // Add is-active class to the clicked tabs--link
        $(this).addClass('is-active');
      });
    }

    if ($('body').is('.localization-dashboard')) {
      // Add's datepicker to the create announcement pop-up
      addDatePicker('#id_show_after');
      addDatePicker('#id_show_until');
    }

    // product selector page reloading
    $('#product-selector select').on('change', function() {
      var val = $(this).val();
      var queryParams = getQueryParamsAsDict(document.location.toString());

      if (val === '') {
        delete queryParams.product;
      } else {
        queryParams.product = val;
      }
      document.location = document.location.pathname + '?' + $.param(queryParams);
    });
  });

  function addDatePicker(inputId) {
    $(inputId).attr('type','text').datepicker('option', 'dateFormat', 'yy-mm-dd');
  }

})(jQuery);
