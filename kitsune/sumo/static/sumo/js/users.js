/*
 * users.js
 * Make public emails clickable.
 */
import Modal from "protocol/js/modal";

function makeEmailsClickable() {
  document.querySelectorAll('.email').forEach(function (el) {
    var emailVal = el.textContent;
    var a = document.createElement('a');
    a.setAttribute('href', 'mailto:' + emailVal);
    a.textContent = emailVal;
    el.replaceChildren(a);
  });
}

var CONFIRM_TEXT = gettext('WARNING! Are you sure you want to deactivate this user? This cannot be undone!');
function confirmUserDeactivation() {
  document.querySelectorAll('.deactivate').forEach(function (form) {
    form.addEventListener('submit', function (e) {
      if (!confirm(CONFIRM_TEXT)) {
        e.preventDefault();
      }
    });
  });
}

function handleAccountDeletion() {
  // Handle the delete account button click
  var button = document.getElementById('delete-profile-button');
  if (!button) {
    return;
  }
  button.addEventListener('click', function (e) {
    e.preventDefault();

    var form = button.closest('form');

    // Close the modal.
    Modal.closeModal();

    // Directly submit the form after a small delay. This ensures the modal
    // closing completes before submission.
    setTimeout(function () {
      if (form) {
        form.submit();
      }
    }, 50);
  });
}

function init() {
  makeEmailsClickable();
  confirmUserDeactivation();
  handleAccountDeletion();
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}
