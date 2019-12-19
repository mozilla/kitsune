(function() {
  'use strict';
  var modalLink = document.querySelectorAll('[data-sumo-modal]');
  if (modalLink) {
    modalLink.forEach(function(e) {
      var dialogLink = e.dataset.sumoModal;
      var content = document.getElementById(dialogLink);
      console.log('dialogLink', dialogLink);
      console.log('content', content);
      function openThisDialog(e){
        Mzp.Modal.createModal(e.target, content, {
          closeText: 'Close modal',
          content: document.getElementById(e.target.dataset.sumoModal),
          onCreate: function() {
            console.log('Modal opened');
          },
          onDestroy: function() {
            console.log('Modal closed');
          }
        });
        e.preventDefault();
      };
      e.addEventListener("click", openThisDialog);
    });
  }
})();
