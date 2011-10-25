/*
 * A tag autocomplete widget.
 */

(function($) {

"use strict";

function init() {
    var $input = $('input.tags-autocomplete');
    $input.each(function() {
        var $this = $(this),
            vocab = $this.data('vocabulary');
        $this.betterautocomplete({
            minChars: 1,
            delimiter: /(,)\s*/,
            width: 200,
            lookup: _.keys(vocab),
            onSelect: function(value) {
                $this.trigger('selected', [value, vocab[value]]);
            }
        });
    });
}

$(document).ready(init);

}(jQuery));
