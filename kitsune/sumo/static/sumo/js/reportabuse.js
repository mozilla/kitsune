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

          // The radios are positioned off-screen by our styles, so the
          // browser's own validation bubble would be invisible. Report the
          // problem in the modal instead, and leave the form up to retry.
          if (!form.checkValidity()) {
            var invalidField = form.querySelector(':invalid');
            showMessage(
              form,
              (invalidField && invalidField.validationMessage) ||
                gettext('Please complete all required fields.')
            );
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
            .catch(function (error) {
              showMessage(
                form,
                (error && error.body && error.body.message) ||
                  gettext('There was an error. Please try again in a moment.')
              );
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
