import trackEvent from "sumo/js/analytics";
import { apiFetch } from "sumo/js/utils/fetch";

(function() {
  var match = document.cookie.match(/(?:^|; )geoip_country_name=([^;]*)/);
  var value = match ? match[1] : '';
  // SimpleCookie wraps values with special chars (e.g. spaces in country names) in double quotes
  if (value.length >= 2 && value.charAt(0) === '"' && value.charAt(value.length - 1) === '"') {
    value = value.slice(1, -1);
  }
  handleLocale(value);
})();

export function handleLocale(countryName) {
  // Mapping of {currentLocale: {country_name: suggested_locale}}
  var languageSuggestions = {
    'en-US': {
      Indonesia: 'id',
      Bangladesh: 'bn',
    },
  };

  var currentLocale = document.documentElement.lang;
  var suggestedLocale = (languageSuggestions[currentLocale] || {})[countryName];
  var announceBar = document.getElementById('announce-geoip-suggestion');

  if (!announceBar) {
    return;
  }

  if (suggestedLocale) {
    /* Now get the localized versions of the prompt and response texts from
    * the server. This can't be done with the normal localization route,
    * because the localization the server gave won't have the suggested locale
    * in it. The non-suggested text could be translated locally, but the code
    * is cleaner when it is also translated on the server.
    */
    apiFetch('/geoip-suggestion', {
      method: 'GET',
      data: {
        locales: [currentLocale, suggestedLocale],
      },
      dataType: 'json',
    })
      .then(function(data) {
        /* Get the translated strings in both the current language and the
        * new (suggested) language. Show a prompt to switch to the new
        * language in both languages, but only if the prompts are different.
        * If the prompt is not localized, it will only show in the current
        * language, instead of repeating the same message twice.
        */
        var languageInCurrentLocale = data.locales[suggestedLocale][0];
        var languageInNativeLocale = data.locales[suggestedLocale][1];

        var currentLocaleSuggestion = interpolate(
          data[currentLocale].suggestion,
          {language: languageInCurrentLocale},
          true);
        var suggestedLocaleSuggestion = interpolate(
          data[suggestedLocale].suggestion,
          {language: languageInNativeLocale},
          true);

        announceBar.style.display = 'block';
        var message = announceBar.querySelector('p');

        message.textContent = currentLocaleSuggestion;
        message.appendChild(makeButton('confirm', data[currentLocale].confirm));
        message.appendChild(makeButton('cancel', data[currentLocale].cancel));

        if (data[currentLocale].suggestion !== data[suggestedLocale].suggestion) {
          var localisedMessage = document.createElement('p');
          announceBar.appendChild(localisedMessage);
          localisedMessage.textContent = suggestedLocaleSuggestion;
          localisedMessage.appendChild(makeButton('confirm', data[suggestedLocale].confirm));
          localisedMessage.appendChild(makeButton('cancel', data[suggestedLocale].cancel));
        }

        trackEvent('geoip_targeting_banner_show');
      })
      .catch(function(err) {
        console.error('GeoIP suggestion error', err);
      });

    announceBar.addEventListener('click', function(ev) {
      /* If the user clicks "yes", close the bar (so it remembers) and navigate
      * to the new locale. If the user clicks "no", just close the bar.
      * Either way, the announce bar UI code (in ui.js) will remember this action
      * in local storage, so the bar won't ever show up again.
      */
      var button = ev.target.closest('p button');
      if (!button) {
        return;
      }
      var closeButton = announceBar.querySelector('.close-button');
      if (closeButton) {
        closeButton.click();
      }
      if (button.classList.contains('confirm')) {
        trackEvent('geoip_targeting_banner_accept');
        // Delay the click navigation by 250ms to ensure the event is tracked.
        setTimeout(function() {
          var newQsVar = 'lang=' + suggestedLocale;
          if (window.location.search.length === 0) {
            newQsVar = '?' + newQsVar;
          } else {
            newQsVar = '&' + newQsVar;
          }
          window.location.search += newQsVar;
        }, 250);
      } else {
        trackEvent('geoip_targeting_banner_reject');
      }
    });

  } else {
    // If no locale should be suggested, the bar might still display, so remove it.
    announceBar.remove();
  }
}

function makeButton(kind, text) {
  var button = document.createElement('button');
  button.className = 'sumo-button button-sm ' + kind;
  button.textContent = text;
  return button;
}
