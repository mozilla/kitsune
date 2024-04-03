import "sumo/js/protocol";
import trackEvent from "sumo/js/analytics";

(function() {
  'use strict';
  // a custom callback can be passed to the lang switcher for analytics purposes.
  Mzp.LangSwitcher.init(function(previousLanguage, newLanguage) {
    trackEvent("footer.language-switcher", {
      "old_language": previousLanguage,
      "new_language": newLanguage,
    });
  })
})();
