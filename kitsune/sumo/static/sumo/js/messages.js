import { autoResize } from "sumo/js/utils/autoresize";
import AjaxPreview from "sumo/js/ajaxpreview";
import Marky from "sumo/js/markup";

/*
 * Make textarea in replies auto expanding.
 * Private messaging.
 */

function hideAll(selector) {
  document.querySelectorAll(selector).forEach(function (el) {
    el.style.display = "none";
  });
}

function showAll(selector) {
  document.querySelectorAll(selector).forEach(function (el) {
    el.style.display = "";
  });
}

function init() {
  // Show the ajax preview on the new message page.
  Marky.createSimpleToolbar('#new-message .editor-tools', '#id_message');
  new AjaxPreview(document.getElementById('preview-btn'), {
    changeHash: false,
  });

  // Hide reply button and shrink the textarea.
  var area = document.querySelector('#read-message textarea#id_message');
  if (area) {
    area.setAttribute('placeholder', gettext('Reply...'));
    hideAll('#read-message .editor-tools');
    hideAll('#read-message input[type=submit]');

    // Show the original button and expanding textarea.
    area.addEventListener('focus', function () {
      autoResize(area, { minHeight: 150 });
      area.classList.add('focused');
      showAll('#read-message .editor-tools');
      showAll('#read-message input[type=submit]');
      Marky.createSimpleToolbar('#read-message .editor-tools', '#id_message', { privateMessaging: true });
      new AjaxPreview(document.getElementById('preview-btn'), {
        changeHash: false,
      });
    }, { once: true });
  }

  // Character counter for message box.
  var summaryCount = document.getElementById('remaining-characters');
  var summaryBox = summaryCount ? document.querySelector(summaryCount.dataset.input) : null;
  if (summaryCount && summaryBox) {
    var maxCount = parseInt(summaryCount.dataset.maxCharacters, 10);
    var updateCount = function () {
      var currentCount = summaryBox.value.length;
      var delta = maxCount - currentCount;

      if (delta < 0) {
        delta = 0;
      }
      var message = interpolate(gettext('%s characters remaining'), [delta]);
      summaryCount.textContent = message;
      if (maxCount - currentCount >= 10) {
        summaryCount.style.color = 'black';
      } else {
        summaryCount.style.color = 'red';
        if (currentCount >= maxCount) {
          summaryBox.value = summaryBox.value.substr(0, maxCount);
        }
      }
    };

    updateCount();
    summaryBox.addEventListener('input', updateCount);
  }
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}
