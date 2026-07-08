import { getQueryParamsAsDict } from "sumo/js/main";

/*
 * kb dashboard chart
 */

function onReady() {
  if (document.body.classList.contains('contributor-dashboard')) {
    // Add click events to the date tabs
    document.querySelectorAll('.tabs--link').forEach(function (link) {
      link.addEventListener('click', function () {
        // Clear active class from all tabs--link
        document.querySelectorAll('.tabs--link').forEach(function (other) {
          other.classList.remove('is-active');
        });
        // Add is-active class to the clicked tabs--link
        link.classList.add('is-active');
      });
    });
  }

  if (document.body.classList.contains('localization-dashboard')) {
    // Native date pickers for the create-announcement popup. Native date
    // inputs use ISO (yyyy-mm-dd) values, matching the old datepicker format.
    useNativeDate('#id_show_after');
    useNativeDate('#id_show_until');
  }

  // product selector page reloading
  var selector = document.querySelector('#product-selector select');
  if (selector) {
    selector.addEventListener('change', function () {
      var val = selector.value;
      var queryParams = getQueryParamsAsDict(document.location.toString());

      if (val === '') {
        delete queryParams.product;
      } else {
        queryParams.product = val;
      }
      document.location = document.location.pathname + '?' +
        new URLSearchParams(queryParams).toString();
    });
  }
}

function useNativeDate(selector) {
  var input = document.querySelector(selector);
  if (input) {
    input.type = 'date';
  }
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', onReady);
} else {
  onReady();
}
