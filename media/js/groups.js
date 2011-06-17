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
    $('.editable a.edit').each(function() {
        var $this = $(this),
            originalText = $this.text();
        $this.click(function(ev){
            var $container = $this.closest('.editable');
            $container.toggleClass('edit-on');
            if ($container.hasClass('edit-on')) {
                $this.text(gettext('Cancel'));
            } else {
                $this.text(originalText);
            }
            ev.preventDefault();
        });
    });
}

$(document).ready(init);

}(jQuery));
