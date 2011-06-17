/*
 * JS for Groups app
 */

(function($) {

"use strict";

function init() {
    // Marky for information edit:
    var buttons = Marky.allButtonsExceptShowfor();
    Marky.createCustomToolbar('.editor-tools', '#id_information', buttons);

    initInlineEditing();
}

function initInlineEditing() {
    // Enable managing of member and leader lists.
    $('.editable a.edit').click(function(ev){
        ev.preventDefault();
        $(this).hide().closest('.editable').addClass('edit-on');
    });
}

$(document).ready(init);

}(jQuery));
