import "sumo/js/protocol";
import trackEvent from "sumo/js/analytics";
import SumoLanguageSwitcher from "sumo/js/sumo-language-switcher";

(function() {
  'use strict';
  // Initialize our custom language switcher with analytics callback
  const langSwitcher = new SumoLanguageSwitcher();
  langSwitcher.init(function(previousLanguage, newLanguage) {
    trackEvent("footer.language-switcher", {
      "old_language": previousLanguage,
      "new_language": newLanguage,
    });
  });
})();
