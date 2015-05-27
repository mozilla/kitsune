/*
 * A tag filtering form.
 */

(function($) {

"use strict";

function init($container) {
    var $form = $container ? $container.find('form') : $('#tag-filter form'),
        $tags = $form.find('input[type="text"]'),
        $btn = $form.find('input[type="submit"], button'),
        $hidden = $('<input type="hidden"/>'),
        vocab = $tags.data('vocabulary'),
        lowerVocab = {};

    if (!$form.length) {
        return;
    }

    // Create a lower case vocab for case insensitive match.
    _.each(_.keys(vocab), function(name) {
        lowerVocab[name.toLowerCase()] = vocab[name];
    });

    // Add a hidden field for comma-separated slugs.
    $hidden.attr('name', $tags.attr('name'))
           .appendTo($form);
    $tags.removeAttr('name');

    // Disable button while text input is empty.
    $btn.attr('disabled', 'disabled');
    $tags.keyup(function() {
        if ($tags.val()) {
            $btn.removeAttr('disabled');
        } else {
            $btn.attr('disabled', 'disabled');
        }
    });

    // Set up autocomplete
    // Skip if the autocomplete plugin isn't available (qunit tests).
    if($tags.autocomplete) {
        $tags.autocomplete({
            source: _.keys(vocab),
            delay: 0,
            minLength: 1
        });
    }

    // When form is submitted, get the slugs to send over in request.
    $form.submit(function() {
        var tagNames = $tags.val(),
            slugNames = [],
            currentSlugs = $form.find('input.current-tagged').val(),
            slugs,
            invalid = false;

        // For each tag name, find the slug.
        _.each(tagNames.split(','), function(tag) {
            var trimmed = $.trim(tag),
                slug = lowerVocab[trimmed.toLowerCase()];
            if (slug) {
                slugNames.push(slug);
            } else if (trimmed) {
                invalid = true;
                alert(interpolate(gettext('Invalid tag entered: %s'), [tag]));
            }
        });

        // Invalid or no tags? No requests!
        if (invalid || slugNames.length === 0) {
            $form.trigger('ajaxComplete');
            if (!invalid) {
                alert(gettext('No tags entered.'));
            }
            return false;
        }
        slugs = slugNames.join(',');

        // Prepend any existing filters applied.
        if (currentSlugs) {
            slugs = currentSlugs + ',' + slugs;
        }
        $hidden.val(slugs);
    });
}

k.TagsFilter = {
    init: init
};

$(document).ready(function() {
    k.TagsFilter.init();
});

}(jQuery));
