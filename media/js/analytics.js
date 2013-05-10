var _gaq = _gaq || [];
var extraPush = $('body').data('ga-push');
var alternateUrl = $('body').data('ga-alternate-url');

_gaq.push(['_setAccount', 'UA-36116321-2']);

// Add any extra pushes from body[data-ga-push].
if (extraPush && extraPush.length) {
  for (var i = 0, l = extraPush.length; i < l; i++) {
    _gaq.push(extraPush[i]);
  }
}

if (alternateUrl) {
  _gaq.push(['_trackPageview', alternateUrl]);
} else {
  _gaq.push(['_trackPageview']);
}


(function() {
  var ga = document.createElement('script');
  ga.type = 'text/javascript';
  ga.async = true;
  if (document.location.protocol === 'https:') {
    ga.src = 'https://ssl.google-analytics.com/ga.js';
  } else {
    ga.src = 'http://www.google-analytics.com/ga.js';
  }
  var s = document.getElementsByTagName('script')[0];
  s.parentNode.insertBefore(ga, s);
})();


// Additional tracking:
$(document).ready(function() {
  // Track clicks to the product download button:
  $(document).on('click', 'a.download-button', function(ev) {
    ev.preventDefault();

    var pathParts = document.location.pathname.split('/');
    var productSlug = pathParts[pathParts.length - 1];

    _gaq.push(['_trackEvent', 'Download Click', productSlug]);

    // Delay the outbound click by 100ms to ensure the event is tracked.
    var href = $(this).attr('href');
    setTimeout(function() {
      document.location.href = href;
    }, 100);
  });
});
