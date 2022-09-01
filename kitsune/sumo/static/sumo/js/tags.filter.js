import "jquery-ui/ui/widgets/autocomplete";
import _each from "underscore/modules/each";
import _keys from "underscore/modules/keys";

/*
 * A tag filtering form.
 */

function init($container) {
  var $form = $container ? $container.find('form') : $('#tag-filter form'),
    $tags = $form.find('input[type="text"]'), $btn = $form.find('input[type="submit"], button'),
    $hidden = $('<input type="hidden"/>'),
    vocab = $tags.data('vocabulary'),
    lowerVocab = {};

  if (!$form.length) {
    return;
  }

  // Create a lower case vocab for case insensitive match.
  _each(_keys(vocab), function(name) {
    lowerVocab[name.toLowerCase()] = vocab[name];
  });

  // Add a hidden field for comma-separated slugs.
  $hidden.attr('name', $tags.attr('name'))
  .appendTo($form);
  $tags.removeAttr('name');

  // Disable button while text input is empty.
  $btn.attr('disabled', 'disabled');
  $tags.on('keyup', function() {
    if ($tags.val()) {
      $btn.prop("disabled", false);
    } else {
      $btn.attr('disabled', 'disabled');
    }
  });

  // Set up autocomplete
  // Skip if the autocomplete plugin isn't available (unit tests).
  if ($tags.autocomplete) {
    $tags.autocomplete({
      source: _keys(vocab),
      delay: 0,
      minLength: 1
    });
  }

  // When form is submitted, get the slugs to send over in request.
  $form.on("submit", function() {
    var tagNames = $tags.val(),
      slugNames = [],
      currentSlugs = $form.find('input.current-tagged').val(),
      slugs,
      invalid = false;

    // For each tag name, find the slug.
    _each(tagNames.split(','), function(tag) {
      var trimmed = tag.trim(),
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

const TagsFilter = {
  init: init
};
export default TagsFilter;

$(function() {
  TagsFilter.init();
});
