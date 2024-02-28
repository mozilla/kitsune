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
        return safeInterpolate('<li><div class="name_search">%(value)s</div></li>', {value: item[valueField]}, true);
      },
      onAdd: function (item) {
        $(this).closest('.single').closest('form').submit();
      }
    };

    $(`input${selector}`).tokenInput(options.apiEndpoint, tokenInputSettings);
  }

  // Initialize autocomplete for groups
  $(function() {
    initAutocomplete({
      selector: '.group-autocomplete',
      apiEndpoint: $('body').data('groupnames-api'),
      valueField: 'groupname',
      hintText: 'Search for a group...',
      resultsFormatter: function(item) {
        return safeInterpolate('<li><div class="groupname_search">%(groupname)s</div></li>', item, true);
      }
    });
  });

  // Initialize autocomplete for users
  $(function() {
    initAutocomplete({
      selector: '.user-autocomplete',
      apiEndpoint: $('body').data('usernames-api'),
      valueField: 'username',
      displayField: 'display_name', // Optional, used if different from valueField
      hintText: 'Search for a user...',
      resultsFormatter: function(item) {
        if (item.display_name) {
          return safeInterpolate('<li><img src="%(avatar)s"/><div class="name_search">%(display_name)s [%(username)s]</div></li>', item, true);
        }
        return safeInterpolate('<li><img src="%(avatar)s"/><div class="name_search">%(username)s</div></li>', item, true);
      }
    });
  });

})(jQuery);
