/* globals $:false, _dntEnabled:false */

(function($) {
  'use strict';
  // Track clicks to form buttons with data-event-category attr.
  $('body').on('click', 'button[data-event-category]', function(ev) {
    ev.preventDefault();

    var $this = $(this);
    trackEvent(
      $this.attr('data-event-category'),
      $this.attr('data-event-action'),
      $this.attr('data-event-label'),
      $this.attr('data-event-value')
    );

    // Delay the form post by 250ms to ensure the event is tracked.
    setTimeout(function() {
      $this.closest('form').submit();
    }, 250);

    return false;
  });

  // Track clicks to links with data-event-category attr.
  $('body').on('click', 'a[data-event-category]', function(ev) {
    ev.preventDefault();

    var $this = $(this);
    var href = $this.attr('href');

    trackEvent(
      $this.attr('data-event-category'),
      $this.attr('data-event-action'),
      $this.attr('data-event-label'),
      $this.attr('data-event-value')
    );

    // Delay the click navigation by 250ms to ensure the event is tracked.
    setTimeout(function() {
      document.location.href = href;
    }, 250);

    return false;
  });
})(jQuery);

function trackEvent(category, action, label, value) {
  if (window.gtag) {
    window.gtag('event', action, {
      'event_category': category,
      'event_label': label,
      'value': value
    });
  }
}
