$(function() {
  var selectTrigger = $('.ts-select-trigger');
  var options = $('.ts-options');
  var showSelected = false;

  function setSelectedItem(selected) {
    var items = options.find('a');
    var parentContainer = selected.parents('.selector');

    items.each(function() {
      $(this).removeClass('selected')
      .removeAttr('aria-checked');
    });

    selected.addClass('selected');
    selected.attr('aria-checked', 'true');

    // Determine whether the widget should behave like a standard
    // select element.
    if (parentContainer.data('emulate-select')) {
      parentContainer.find('.currently-selected').text(selected.text());
      // Set the value of the hidden element to the selected value.
      $('#ts-value').val(selected.data('value'));
    }
  }

  function hideOptions() {
    // Move focus back to the trigger/button
    selectTrigger[0].focus();
    options.parents('.select-options').hide();
  }

  // Show/Hide the options
  selectTrigger.on('click', function(event) {
    event.preventDefault();

    var parentContainer = $(this).parents('.selector');
    var optionsFilter = $('.options-filter');
    var optionsContainer = parentContainer.find('.select-options');
    var expanded = optionsContainer.attr('aria-expanded');

    optionsContainer.toggle();
    // Update ARIA expanded state
    optionsContainer.attr('aria-expanded', expanded === 'false' ? 'true' : 'false');
    // Move focus to options container if expanded
    if (expanded === 'false') {
      $('.ts-options', optionsContainer)[0].focus();
    }

    // Show or hide the filter field.
    if (optionsFilter.data('active')) {
      optionsFilter.toggle();
    }
  });

  options.on('click', 'a', function(event) {
    event.stopPropagation();
    setSelectedItem($(this));
    hideOptions();
  });

  window.addEventListener('keyup', function(event) {
    // 'key' is the standard but has not been implemented in Gecko
    // yet, see https://bugzilla.mozilla.org/show_bug.cgi?id=680830
    // so, we check both.
    var keyPressed = event.key || event.keyCode;
    // esc key pressed.
    if (keyPressed === 27 || keyPressed === 'Esc') {
      hideOptions();
    }
  });
});
