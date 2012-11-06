var _gaq = _gaq || [];

_gaq.push(['_setAccount', 'UA-36116321-2']);
_gaq.push(['_trackPageview']);

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
