// Collect wiki metrics.

(function ($) {

    function init() {
        // Collect some metrics on the Article page.
        if (!$('body').is('.document')) {
            return;
        }

        // Track showfor changes in Google Analytics:
        $('#os').change(function() {
            if (_gaq) {
                _gaq.push(['_trackEvent',
                           'ShowFor Switch',
                           'OS - ' + $(this).val(),
                           getEnglishSlug() + ' / ' + getLocale()]);
            }
        });

        $('#browser').change(function() {
            if (_gaq) {
                _gaq.push(['_trackEvent',
                           'ShowFor Switch',
                           'Version - ' + $(this).val(),
                           getEnglishSlug() + ' / ' + getLocale()]);
            }
        });

        // Fire an event after 10 seconds to track "read".
        setTimeout(function() {
            if (_gaq) {
                _gaq.push(['_trackEvent',
                           'Article Read',
                           getEnglishSlug() + ' / ' + getLocale()]);
            }
        }, 10000);

        function getLocale() {
            return $('html').attr('lang');
        }

        function getEnglishSlug() {
            return $('body').data('default-slug');
        }
    }

    $(document).ready(init);

}(jQuery));
