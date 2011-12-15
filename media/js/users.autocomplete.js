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
        term = (term+'').replace(/([\\\.\+\*\?\[\^\]\$\(\)\{\}\=\!\<\>\|\:])/g, "\\$1")
        var regex = new RegExp( '(' + term + ')', 'gi' );
        return string.replace(regex, "<strong>$1</strong>")
    }

    $('input.user-autocomplete').tokenInput($('body').data('usernames-api'),
    {
        theme: "facebook",
        hintText: "Search for a user...",
        queryParam: "term",
        propertyToSearch: "username",
        tokenValue: "username",
        resultsFormatter: function(item){
        var term = $("#token-input-id_to").val()
            return ("<li><div style='display: inline-block; padding-left: 10px;'><div class='username'>" +
                    item.username +  "</div><div class='email'>" +
                    wrapTerm(item.email, term) + "</div></div></li>")
        },

    });

}

$(document).ready(init);

}(jQuery));
