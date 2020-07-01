(function () {
  "use strict";
  // a custom callback can be passed to the lang switcher for analytics purposes.
  Mzp.LangSwitcher.init(function (previousLanguage, newLanguage) {
    console.log("Previous language: ", previousLanguage);
    console.log("New language: ", newLanguage);
  });
})();
