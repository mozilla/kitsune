/*
 * users.autocomplete.js
 * A username autocomplete widget.
 */

(function($) {

"use strict";
function extractLast(term) {
    return term.split(/,\s*/).pop();
}

function init() {
    var cache = {}, lastXhr;
    $('input.user-autocomplete').autocomplete({
        source: function(request, response) {
            var serviceUrl = $('body').data('usernames-api');
            $.getJSON(serviceUrl, {
                term: extractLast(request.term)
            }, response);
        },
        focus: function(event, ui) {
            return false;
        },
        select: function(event, ui) {
            $(event.target).val(ui.item.username);
            return false;
        }
    });
}

$(document).ready(init);

}(jQuery));
