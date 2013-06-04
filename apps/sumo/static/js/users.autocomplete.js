/*
 * users.autocomplete.js
 * A username autocomplete widget.
 */

(function($) {

"use strict";

function init() {


    function wrapTerm(string, term) {
        /*
         * Wraps the term in <strong> tags.
         * Crazy regex for characters that have signifigance in regex, not
         * they they should be in usernames or emails.
         */
        term = (term+'').replace(/([\\\.\+\*\?\[\^\]\$\(\)\{\}\=\!\<\>\|\:])/g, "\\$1");
        var regex = new RegExp( '(' + term + ')', 'gi' );
        return string.replace(regex, "<strong>$1</strong>");
    }

    var prefill = [];

    if($("#id_to").val()) {
        prefill = [{username: $("#id_to").val(), display_name: null}];
    }

    var tokenInputSettings = {
        theme: "facebook",
        hintText: gettext("Search for a user..."),
        queryParam: "term",
        propertyToSearch: "username",
        tokenValue: "username",
        prePopulate: prefill,
        resultsFormatter: function(item){
            var term = $("#token-input-id_to").val();
            if (item.display_name) {
                return k.safeInterpolate('<li><div class="name_search">%(display_name)s [%(username)s]</div></li>', item, true);
            }
            return k.safeInterpolate('<li><div class="name_search">%(username)s</div></li>', item, true);
        },
        onAdd: function (item) {
            $(this).closest('.single').closest('form').submit();
        }
    };

    $('input.user-autocomplete').tokenInput($('body').data('usernames-api'), tokenInputSettings);
};

$(document).ready(init);

}(jQuery));
