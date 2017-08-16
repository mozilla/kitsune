(function() {
  var isFirefox = function () {
    var userAgent = navigator.userAgent.toLowerCase();
    return userAgent.includes('firefox');
  };

  if (!isFirefox()) {
    /* remove the hide class from the download button as the browser is not firefox */
    var fxDownloadButton = document.getElementsByClassName('firefox-download-button')[0];
    fxDownloadButton.classList.remove('hidden');
  }

})();
