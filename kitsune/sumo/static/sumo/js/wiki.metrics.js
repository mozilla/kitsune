/* globals _gaq:false, trackEvent:false, jQuery:false */
// Collect wiki metrics.

(function ($) {

  function init() {
    // Collect some metrics on the Article page.
    if (!$('body').is('.document')) {
      return;
    }

    // Collect metrics on article votes.
    $(document).on('vote', function(t, data) {
      var value;
      if (_gaq) {
        if ('helpful' in data) {
          value = 'Helpful';
        } else if ('not-helpful' in data) {
          value = 'Not Helpful';
        } else {
          // This isn't the kb vote form.
          // (It's the survey or some other ajax form.)
          return;
        }

        trackEvent('Article Vote',
                   data.source + ' - ' + value,
                   getEnglishSlug() + ' / ' + getLocale());
      }
    });

    // Track showfor changes in Google Analytics:
    $('#os').change(function() {
      trackEvent('ShowFor Switch',
                 'OS - ' + $(this).val(),
                 getEnglishSlug() + ' / ' + getLocale());

    });

    $('#browser').change(function() {
      trackEvent(
        'ShowFor Switch',
        'Version - ' + $(this).val(),
        getEnglishSlug() + ' / ' + getLocale());
    });

    // Fire an event after 10 seconds to track "read".
    setTimeout(function() {
      trackEvent(
        'Article Read',
        getEnglishSlug() + ' / ' + getLocale());
    }, 10000);

    function getLocale() {
      return $('html').attr('lang');
    }

    function getEnglishSlug() {
      return $('body').data('default-slug');
    }
  }

  $(document).ready(init);

})(jQuery);
