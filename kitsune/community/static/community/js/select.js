export function init() {
  var selectTriggers = document.querySelectorAll('.ts-select-trigger');
  var optionLists = document.querySelectorAll('.ts-options');

  function setSelectedItem(selected) {
    var parentContainer = selected.closest('.selector');

    // Clear the selected state across all option lists (matches the original,
    // which operated on the global $('.ts-options') set).
    optionLists.forEach(function(list) {
      list.querySelectorAll('a').forEach(function(item) {
        item.classList.remove('selected');
        item.removeAttribute('aria-checked');
      });
    });

    selected.classList.add('selected');
    selected.setAttribute('aria-checked', 'true');

    // Determine whether the widget should behave like a standard
    // select element.
    if (parentContainer && parentContainer.dataset.emulateSelect) {
      var current = parentContainer.querySelector('.currently-selected');
      if (current) {
        current.textContent = selected.textContent;
      }
      // Set the value of the hidden element to the selected value.
      var hidden = document.getElementById('ts-value');
      if (hidden) {
        hidden.value = selected.dataset.value;
      }
    }
  }

  function hideOptions() {
    // Move focus back to the trigger/button
    if (selectTriggers[0]) {
      selectTriggers[0].focus();
    }
    optionLists.forEach(function(list) {
      var container = list.closest('.select-options');
      if (container) {
        container.style.display = 'none';
      }
    });
  }

  // Show/Hide the options
  selectTriggers.forEach(function(trigger) {
    trigger.addEventListener('click', function(event) {
      event.preventDefault();

      var parentContainer = trigger.closest('.selector');
      if (!parentContainer) {
        return;
      }
      var optionsFilter = document.querySelector('.options-filter');
      var optionsContainer = parentContainer.querySelector('.select-options');
      if (!optionsContainer) {
        return;
      }
      var expanded = optionsContainer.getAttribute('aria-expanded');

      toggleDisplay(optionsContainer);
      // Update ARIA expanded state
      optionsContainer.setAttribute('aria-expanded', expanded === 'false' ? 'true' : 'false');
      // Move focus to options container if expanded
      if (expanded === 'false') {
        var list = optionsContainer.querySelector('.ts-options');
        if (list) {
          list.focus();
        }
      }

      // Show or hide the filter field.
      if (optionsFilter && optionsFilter.dataset.active) {
        toggleDisplay(optionsFilter);
      }
    });
  });

  optionLists.forEach(function(list) {
    list.addEventListener('click', function(event) {
      var link = event.target.closest('a');
      if (!link || !list.contains(link)) {
        return;
      }
      event.stopPropagation();
      setSelectedItem(link);
      hideOptions();
    });
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
}

// Toggle an element hidden-by-CSS-display:none on/off (jQuery .toggle equivalent).
function toggleDisplay(el) {
  var hidden = window.getComputedStyle(el).display === 'none';
  el.style.display = hidden ? 'block' : 'none';
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}
