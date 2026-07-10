/*
* Report abuse UI.
*/

import { apiFetch } from "sumo/js/utils/fetch";
import { serialize, slideUp } from "sumo/js/utils/dom";

export function init() {
  document.querySelectorAll('[data-sumo-modal]').forEach(function (modalToggle) {
    var identifier = modalToggle.dataset.sumoModal;
    document
      .querySelectorAll('[data-modal-id="' + identifier + '"] [type="submit"]')
      .forEach(function (submitButton) {
        submitButton.addEventListener('click', function (ev) {
          ev.preventDefault();
          var form = submitButton.closest('form');
          if (!form) {
            return;
          }

          apiFetch(form.getAttribute('action'), {
            method: 'POST',
            data: serialize(form),
            dataType: 'json',
          })
            .then(function (data) {
              showMessage(form, data.message);
              slideUp(form);
            })
            .catch(function () {
              showMessage(
                form,
                gettext('There was an error. Please try again in a moment.')
              );
              slideUp(form);
            });
        });
      });
  });
}

function showMessage(form, text) {
  if (!form.parentNode) {
    return;
  }
  Array.from(form.parentNode.children).forEach(function (sibling) {
    if (sibling !== form && sibling.matches('.message')) {
      sibling.textContent = text;
    }
  });
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}
