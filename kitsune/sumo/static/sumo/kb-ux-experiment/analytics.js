document.addEventListener('DOMContentLoaded', function() {

  var helpful = document.querySelector("input[name='helpful']");
  var not_helpful = document.querySelector("input[name='not-helpful']");
  var video_playback = document.querySelector('video');
  var toc_refs = document.getElementsByClassName('toclevel-ref');
  var contribute_link = document.querySelector('#contribute-button');
  var related_articles = document.getElementsByClassName('related-articles');
  var breadcrumbs = document.getElementsByClassName('breadcrumbs');

  function trackEvent(category, action, label, value) {
    if (window.gtag) {
      window.gtag('event', action, {
        'event_category': category,
        'event_label': label,
        'value': value
      });
    }
  }

  helpful.addEventListener('click', function() {
    trackEvent('kb-articles-experiment feedback', 'helpful article');
  });

  not_helpful.addEventListener('click', function() {
    trackEvent('kb-articles-experiment feedback', 'not helpful article');
  });

  video_playback.addEventListener('play', function() {
    trackEvent('kb-articles-experiment video playback', 'played');
  });

  for (var i=0; i < toc_refs.length; i++) {
    toc_refs[i].addEventListener('click', function() {
      trackEvent('kb-articles-experiment TOC clicked', this.href);
    });
  }

  contribute_link.addEventListener('click', function() {
    trackEvent('kb-articles-experiment conbtribute link', 'clicked');
  });

  for (var x=0; x < related_articles.length; x++) {
    related_articles[x].addEventListener('click', function() {
      trackEvent('kb-articles-experiment Related aricle', this.href);
    });
  }

  breadcrumbs[0].addEventListener('click', function() {
    trackEvent('kb-articles-experiment breadcrumbs menu', 'clicked');
  });
});
