import "sumo/js/libs/jquery.tokeninput";
import { safeString, safeInterpolate } from "sumo/js/main";

/*
 * autocomplete.js
 * A generic autocomplete widget for both groups and users.
 */

(function($) {

  'use strict';

  function initAutocomplete(options) {
    function wrapTerm(string, term) {
      term = (term + '').replace(/([\\\.\+\*\?\[\^\]\$\(\)\{\}\=\!\<\>\|\:])/g, '\\$1');
      var regex = new RegExp( '(' + term + ')', 'gi' );
      return string.replace(regex, '<strong>$1</strong>');
    }

    var prefill = [];
    var selector = options.selector;
    var valueField = options.valueField;

    if ($(selector).val()) {
      prefill = $(selector).val().split(',').map(function(value) {
        var item = {};
        item[valueField] = safeString(value);
        if (options.displayField) {
          item[options.displayField] = safeString(value);
        }
        return item;
      });
    }

    var tokenInputSettings = {
      theme: 'facebook',
      hintText: gettext(options.hintText),
      queryParam: 'term',
      propertyToSearch: valueField,
      tokenValue: valueField,
      prePopulate: prefill,
      resultsFormatter: function(item) {
        var term = $(`token-input-${selector}`).val();
        if (options.resultsFormatter) {
          return options.resultsFormatter(item, term);
        }
        return safeInterpolate('<li><div class="name_search">%(value)s</div></li>', {value: item['type']}, true);
      },
      onAdd: function (item) {
        $(this).closest('.single').closest('form').submit();
      }
    };

    $(`input${selector}`).tokenInput(options.apiEndpoint, tokenInputSettings);
  }

  // Initialize autocomplete for users or groups
  $(function() {
    initAutocomplete({
      selector: '.user-autocomplete',
      apiEndpoint: $('body').data('messages-api'),
      valueField: 'name',
      displayField: 'name',
      hintText: 'Search for a user or group. Group mail requires Staff group membership.',
      placeholder: 'Type a user or group name',
      resultsFormatter: function(item) {
        if ((item.display_name) && (item.type === 'user')) {
          return safeInterpolate('<li class="%(type)s"><img src="%(type_icon)s" alt="icon for %(type)s"><img src="%(avatar)s"/><div class="name_search">%(display_name)s [%(name)s]</div></li>', item, true);
        }
        return safeInterpolate('<li class="%(type)s"><img src="%(type_icon)s" alt="icon for %(type)s"><img src="%(avatar)s"/><div class="name_search">%(name)s</div></li>', item, true);
      }
    });
  });

})(jQuery);
