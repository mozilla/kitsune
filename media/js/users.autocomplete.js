/*
 * users.autocomplete.js
 * A username autocomplete widget.
 */

(function($) {

"use strict";

function init() {
    $('input.user-autocomplete').autocomplete({
        serviceUrl: $('body').data('usernames-api'),
        minChars: 2,
        delimiter: /(,)\s*/,
        width: 250
    });
}

$(document).ready(init);

}(jQuery));
