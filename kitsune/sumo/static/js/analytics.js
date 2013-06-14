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


$('body').on('click', 'a[data-ga-click]', function(ev) {
  ev.preventDefault();

  var $this = $(this);
  // Split by '|', and allow for white space on either side.
  var gaData = $this.data('ga-click').split(/\s*\|\s*/);
  var href = $this.attr('href');

  _gaq.push(gaData);

  // Delay the click navigation by 100ms to ensure the event is tracked.
  setTimeout(function() {
    document.location.href = href;
  }, 100);

  return false;
});
