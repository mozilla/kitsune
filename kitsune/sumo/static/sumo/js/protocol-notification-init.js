(function () {
  "use strict";
  var dissmissButtons = document.querySelectorAll(
    ".mzp-c-notification-bar-button"
  );
  for (var i = 0; i < dissmissButtons.length; i++) {
    dissmissButtons[i].addEventListener(
      "click",
      function (e) {
        e.currentTarget.parentNode.remove();
      },
      false
    );
  }
  var notificationButton = document.querySelector(
    ".mzp-js-notification-trigger"
  );

  if (notificationButton) {
    notificationButton.addEventListener(
      "click",
      function (e) {
        e.preventDefault();
        Mzp.Notification.init(e.target, {
          closeText: "Close notification",
          hasDismiss: true,
        });
      },
      false
    );
  }
})();
