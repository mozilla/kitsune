(function () {
  "use strict";
  Mzp.Navigation.init();
  Mzp.Menu.init();
})();

var toggleNavButtons = document.querySelectorAll("[data-sumo-toggle-nav]");

function resetNavs() {
  var allNavs = document.querySelectorAll(".mzp-c-navigation-items");
  // reset all nav menus
  allNavs.forEach((elm) => {
    elm.setAttribute("aria-expanded", "false");
    elm.classList.remove("mzp-is-open");
  });
}

if (toggleNavButtons.length > 0) {
  toggleNavButtons.forEach((button) => {
    function toggleMenu() {
      var toggleThisId = button.dataset.sumoToggleNav;
      var toggleThisItem = document.querySelector(toggleThisId);

      if (toggleThisItem.getAttribute("aria-expanded") == "false") {
        resetNavs();
        toggleThisItem.classList.add("mzp-is-open");
        toggleThisItem.setAttribute("aria-expanded", "true");

        // if profile nav, go straight to subnav
        if (toggleThisId == "#profile-navigation") {
          toggleThisItem
            .querySelector(".mzp-js-expandable")
            .classList.add("mzp-is-selected");
        }

        // if search nav, focus the field
        if (toggleThisId == "#search-navigation") {
          window.scrollTo(0, 0);
          toggleThisItem.querySelector(".searchbox").focus();
        }
      } else {
        resetNavs();
      }
    }
    button.addEventListener("click", toggleMenu, false);
  });
}

// close navs on resize, but only check width. Height changes on mobile when the
// address bar slides away on scroll, which causes problems.
var timeout = false;
var width = window.innerWidth;
window.addEventListener("resize", function () {
  clearTimeout(timeout);
  timeout = setTimeout(function () {
    if (window.innerWidth != width) {
      width = window.innerWidth;
      resetNavs();
    }
  }, 250);
});

// lang switcher from protocol. #TODO: test this in app.
// (function() {
//   'use strict';
//   // a custom callback can be passed to the lang switcher for analytics purposes.
//   Mzp.LangSwitcher.init(function(
//     previousLanguage, newLanguage) {
//     console.log('Previous language: ',
//       previousLanguage);
//     console.log('New language: ',
//       newLanguage);
//   })
// })();
