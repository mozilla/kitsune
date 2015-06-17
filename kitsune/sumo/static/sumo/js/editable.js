/*
 * Inline editable sections
 */

(function($) {

"use strict";

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

$(document).ready(initInlineEditing);

}(jQuery));
