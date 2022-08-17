import "sumo/js/libs/jquery.tokeninput";
import { safeString, safeInterpolate } from "sumo/js/main";

/*
 * users.autocomplete.js
 * A username autocomplete widget.
 */

(function($) {

  'use strict';

  function init() {


    function wrapTerm(string, term) {
      /*
      * Wraps the term in <strong> tags.
      * Crazy regex for characters that have signifigance in regex, not
      * they they should be in usernames or emails.
      */
      term = (term + '').replace(/([\\\.\+\*\?\[\^\]\$\(\)\{\}\=\!\<\>\|\:])/g, '\\$1');
      var regex = new RegExp( '(' + term + ')', 'gi' );
      return string.replace(regex, '<strong>$1</strong>');
    }

    var prefill = [];

    if ($('#id_to').val()) {
      prefill = $('#id_to').val().split(',').map(function(username) {
        return {username: safeString(username), display_name: null};
      });
    }

    var tokenInputSettings = {
      theme: 'facebook',
      hintText: gettext('Search for a user...'),
      queryParam: 'term',
      propertyToSearch: 'username',
      tokenValue: 'username',
      prePopulate: prefill,
      resultsFormatter: function(item) {
        var term = $('#token-input-id_to').val();
        if (item.display_name) {
          return safeInterpolate('<li><img src="%(avatar)s"/><div class="name_search">%(display_name)s [%(username)s]</div></li>', item, true);
        }
        return safeInterpolate('<li><img src="%(avatar)s"/><div class="name_search">%(username)s</div></li>', item, true);
      },
      onAdd: function (item) {
        $(this).closest('.single').closest('form').submit();
      }
    };

    $('input.user-autocomplete').tokenInput($('body').data('usernames-api'), tokenInputSettings);
  }

  $(init);

})(jQuery);
