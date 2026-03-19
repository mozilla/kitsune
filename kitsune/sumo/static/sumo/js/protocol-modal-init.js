import "sumo/js/protocol";
import Modal from "protocol/js/modal";

(function () {
  'use strict';
  var modalLink = document.querySelectorAll('[data-sumo-modal]');
  if (modalLink) {
    modalLink.forEach(function (e) {
      var dialogLink = e.dataset.sumoModal;
      var content = document.querySelector('[data-modal-id="' + CSS.escape(dialogLink) + '"]');
      function openThisDialog(e) {
        Modal.createModal(e.target, content, {
          closeText: 'Close modal',
          content: document.querySelector('[data-modal-id="' + CSS.escape(e.target.dataset.sumoModal) + '"]'),
        });
        e.preventDefault();
      };
      e.addEventListener("click", openThisDialog);
    });
  }

  var closeButtons = document.querySelectorAll('[data-sumo-modal-close]');
  if (closeButtons) {
    closeButtons.forEach((button) => {
      button.addEventListener("click", () => Modal.closeModal());
    });
  }
})();
