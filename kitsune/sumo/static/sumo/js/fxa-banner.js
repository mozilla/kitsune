(function() {
  'use strict';

  var isFirefox = (/\s(Firefox)/.test(navigator.userAgent));

  if (isFirefox) {
    var banners = ['send', 'monitor', 'sync'];
    var choice = Math.floor(Math.random() * banners.length);
    var copy = document.getElementById('fxa-banner-' + banners[choice]);

    copy.classList.add('chosen');

    setTimeout(function() {
      copy.classList.add('visible');
    }, 100);
  }
})();
