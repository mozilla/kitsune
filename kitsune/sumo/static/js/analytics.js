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


// Track clicks to links with data-ga-click attr.
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

// Track clicks to form buttons with data-ga-click attr.
$('body').on('click', 'button[data-ga-click]', function(ev) {
  ev.preventDefault();

  var $this = $(this);
  // Split by '|', and allow for white space on either side.
  var gaData = $this.data('ga-click').split(/\s*\|\s*/);

  _gaq.push(gaData);

  // Delay the form post by 100ms to ensure the event is tracked.
  setTimeout(function() {
    $this.closest('form').submit();
  }, 100);

  return false;
});


// Track reads (5secs and 10secs on page) of product landing pages.
if ($('body').is('.product-landing')) {
  setTimeout(function() {
    if (_gaq) {
      _gaq.push(['_trackEvent',
                 'Landing Page Read - 10 seconds',
                 $('body').data('product-slug')]);
    }
  }, 10000);

  setTimeout(function() {
    if (_gaq) {
      _gaq.push(['_trackEvent',
                 'Landing Page Read - 5 seconds',
                 $('body').data('product-slug')]);
    }
  }, 5000);
}
