import LangSwitcher from "protocol/js/lang-switcher";
import trackEvent from "sumo/js/analytics";

(function() {
  'use strict';
  LangSwitcher.init(function(previousLanguage, newLanguage) {
    trackEvent("footer.language-switcher", {
      "old_language": previousLanguage,
      "new_language": newLanguage,
    });
  });
})();
