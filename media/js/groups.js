/*
 * JS for Groups app
 */

(function($) {

"use strict";

function init() {
    // Marky for information edit:
    var buttons = Marky.allButtonsExceptShowfor();
    Marky.createCustomToolbar('.editor-tools', '#id_information', buttons);
}

$(document).ready(init);

}(jQuery));
