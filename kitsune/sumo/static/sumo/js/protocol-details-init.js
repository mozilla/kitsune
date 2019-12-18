(function() {
  'use strict';
  var _mqWide = matchMedia('(max-width: 767px)');

  function swapMobileSubnavText(){
    var button = document.querySelector('.details-heading button');
    var activeLinkText = document.querySelector('.sidebar-nav--item .selected').innerHTML;
    button.innerHTML = activeLinkText;
  }

  if (_mqWide.matches) {
    window.Mzp.Details.init('.details-heading');
    swapMobileSubnavText();
  }
  _mqWide.addListener(function(mq) {
    if (mq.matches) {
      window.Mzp.Details.init('.details-heading');
      swapMobileSubnavText();

    } else {
      window.Mzp.Details.destroy('.details-heading');
    }
  });
})();
