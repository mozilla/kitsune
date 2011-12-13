/*
 * users.autocomplete.js
 * A username autocomplete widget.
 */

(function($) {

"use strict";
function split( val ) {
    return val.split( /,\s*/ );
}
function extractLast(term) {
    return split( term ).pop();
}
function wrapTerm(term, string) {
    /*
     * Wraps the term in <strong> tags.
     * Crazy regex for characters that have signifigance in regex, not
     * they they should be in usernames or emails.
     */
    term = (term+'').replace(/([\\\.\+\*\?\[\^\]\$\(\)\{\}\=\!\<\>\|\:])/g, "\\$1")
    var regex = new RegExp( '(' + term + ')', 'gi' );
    return string.replace(regex, "<strong>$1</strong>")
}

function init() {
    var cache = {}, lastXhr;
    $('input.user-autocomplete').autocomplete({
        highlight: true,
        source: function(request, response) {
            var serviceUrl = $('body').data('usernames-api');
            $.getJSON(serviceUrl, {
                term: extractLast(request.term)
            },
            function(data){
                response(_.map(data.suggestions, function(user){
                    return {
                        'value': user.username,
                        'title': user.username,
                        'desc':  user.email
                    }
                }));
            });
        },
        focus: function() {
            // prevent value inserted on focus
            return false;
        },
        select: function( event, ui ) {
            var terms = split( this.value );
            // remove the current input
            terms.pop();
            // add the selected item
            terms.push( ui.item.value );
            // add placeholder to get the comma-and-space at the end
            terms.push( "" );
            this.value = terms.join( ", " );
            return false;
        }
    })
    .data( "autocomplete" )._renderItem = function( ul, item ) {
            return $( "<li></li>" )
                .data( "item.autocomplete", item )
                .append( "<a>" + wrapTerm(this.term, item.label) + "<br>" + wrapTerm(this.term, item.desc) + "</a>" )
                .appendTo( ul );
        };
}

$(document).ready(init);

}(jQuery));
