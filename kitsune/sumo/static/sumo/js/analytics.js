/* globals $:false, _dntEnabled:false */

if (!_dntEnabled()) {
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

  function parseAnalyticsData(data) {
    // Split by ','
    var items = data.split(/,\s*/);
    var results = [];
    $(items).each(function() {
      // Split by '|', and allow for white space on either side.
      results.push(this.split(/\s*\|\s*/));
    });
    return results;
  }

  // Track clicks to links with data-ga-click attr.
  $('body').on('click', 'a[data-ga-click]', function(ev) {
    ev.preventDefault();

    var $this = $(this);
    var gaData = parseAnalyticsData($this.data('ga-click'));
    var href = $this.attr('href');

    $(gaData).each(function() {
      _gaq.push(this);
    });

    // Delay the click navigation by 250ms to ensure the event is tracked.
    setTimeout(function() {
      document.location.href = href;
    }, 250);

    return false;
  });

  // Track clicks to form buttons with data-ga-click attr.
  $('body').on('click', 'button[data-ga-click]', function(ev) {
    ev.preventDefault();

    var $this = $(this);
    var gaData = parseAnalyticsData($this.data('ga-click'));

    $(gaData).each(function() {
      _gaq.push(this);
    });

    // Delay the form post by 250ms to ensure the event is tracked.
    setTimeout(function() {
      $this.closest('form').submit();
    }, 250);

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
}


function trackEvent(category, action, value) {
  if (_gaq) {
    _gaq.push(['_trackEvent', category, action, value]);
  }
}

function trackPageview(value) {
  if (_gaq) {
    _gaq.push(['_trackPageview', value]);
  }
}
