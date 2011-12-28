/*
 * users.autocomplete.js
 * A username autocomplete widget.
 */


// Global to override if needed.
var tokenInputSettings = {};

(function($) {

"use strict";

function init() {


    function wrapTerm(string, term) {
        /*
         * Wraps the term in <strong> tags.
         * Crazy regex for characters that have signifigance in regex, not
         * they they should be in usernames or emails.
         */
        term = (term+'').replace(/([\\\.\+\*\?\[\^\]\$\(\)\{\}\=\!\<\>\|\:])/g, "\\$1")
        var regex = new RegExp( '(' + term + ')', 'gi' );
        return string.replace(regex, "<strong>$1</strong>")
    }

    var tokenInputSettings = {
        theme: "facebook",
        hintText: gettext("Search for a user..."),
        queryParam: "term",
        propertyToSearch: "username",
        tokenValue: "username",
        resultsFormatter: function(item){
            var term = $("#token-input-id_to").val()
            if (item.display_name) {
                return ("<li><div class='name_search'>" +
                        wrapTerm(item.display_name, term) + " [" +item.username +  "]</div></div></li>")
            }
            return ("<li><div class='name_search'>" + item.username + "</div></li>")
        },
        onAdd: function (item) {
            $(this).closest('.single').closest('form').submit();
        }
    };

    $('input.user-autocomplete').tokenInput($('body').data('usernames-api'), tokenInputSettings);
};

$(document).ready(init);

}(jQuery));
