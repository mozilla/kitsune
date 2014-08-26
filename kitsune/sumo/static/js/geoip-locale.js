/* geo.mozilla.org will inject a couple functions that look like this, though
 * with the correct country code/name for the current client.
 *
 *  function geoip_country_code() { return 'US'; }
 *  function geoip_country_name() { return 'United States'; }
 */

(function() {
    // Mapping of {currentLocale: {country_name: suggested_locale}}
    var languageSuggestions = {
        'en-US': {
            Indonesia: 'id',
            Bangladesh: 'bn-BD',
        },
    };

    var currentLocale = $('html').attr('lang');
    var suggestedLocale = (languageSuggestions[currentLocale] || {})[geoip_country_name()];
    var $announceBar = $('#announce-geoip-suggestion');

    if (suggestedLocale) {
        /* Now get the localized versions of the prompt and response texts from
         * the server. This can't be done with the normal localization route,
         * because the localization the server gave won't have the suggested locale
         * in it. The non-suggested text could be translated locally, but the code
         * is cleaner when it is also translated on the server.
         */
        $.ajax({
            method: 'GET',
            url: '/geoip-suggestion',
            data: {
                locales: [currentLocale, suggestedLocale],
            }
        })
        .done(function(data) {
            /* Get the translated strings in both the current language and the
             * new (suggested) language. Show a prompt to switch to the new
             * language in both languages, but only if the prompts are different.
             * If the prompt is not localized, it will only show in the current
             * language, instead of repeating the same message twice.
             */
            var languageInCurrentLocale = data.locales[suggestedLocale][0];
            var languageInNativeLocale =  data.locales[suggestedLocale][1];

            var currentLocaleSuggestion = interpolate(
                data[currentLocale].suggestion,
                {language: languageInCurrentLocale},
                true);
            var suggestedLocaleSuggestion = interpolate(
                data[suggestedLocale].suggestion,
                {language: languageInNativeLocale},
                true);

            var $container = $announceBar.find('.container_12');
            var $message = $container.find('.grid_12');

            $message.append($('<span/>').text(currentLocaleSuggestion));
            $message.append($('<button class="btn confirm" />').text(data[currentLocale].confirm));
            $message.append($('<button class="btn cancel" />').text(data[currentLocale].cancel));

            if (data[currentLocale].suggestion !== data[suggestedLocale].suggestion) {
                $message = $('<div class="grid_12" />').appendTo($container);
                $message.append($('<span/>').text(suggestedLocaleSuggestion));
                $message.append($('<button class="btn confirm" />').text(data[suggestedLocale].confirm));
                $message.append($('<button class="btn cancel" />').text(data[suggestedLocale].cancel));
            }
        })
        .error(function(err) {
            console.error('GeoIP suggestion error', err);
        });

        $announceBar.on('click', '.btn', function(ev) {
            /* If the user clicks "yes", close the bar (so it remembers) and navigate
             * to the new locale. If the user clicks "no", just close the bar.
             * Either way, the announce bar UI code (in ui.js) will remember this action
             * in local storage, so the bar won't ever show up again.
             */
            var $this = $(this);
            $announceBar.find('.close-button').click();
            if ($this.hasClass('confirm')) {
                var newQsVar = 'lang=' + suggestedLocale;
                if (window.location.search.length === 0) {
                    newQsVar = '?' + newQsVar;
                } else {
                    newQsVar = '&' + newQsVar;
                }
                window.location.search += newQsVar;
            }
        });

    } else {
        // If no locale should be suggested, the bar might still display, so remove it.
        $announceBar.remove();
    }

})();
