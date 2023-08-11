import "sumo/js/protocol";


export function collapsibleAccordionInit() {
  'use strict';
  // Initialize any header elements, or header elements wrapped by a "div.for"
  // element (which is generated from the Wiki syntax "{for ...}{/for}") that
  // are direct children of an element with the "mzp-c-details" class.
  for (let hdr of ['h2', 'h3', 'h4', 'h5', 'h6']) {
    window.Mzp.Details.init(`.mzp-c-details > ${hdr}, .mzp-c-details > div.for > ${hdr}`);
  }
}

export default function detailsInit() {
  'use strict';
  var _mqWide = matchMedia('(max-width: 1055px)');

  var sidebarList = document.querySelector('.details-heading');

  function swapMobileSubnavText(){
    var button = document.querySelector('.details-heading button');
    var activeLink = document.querySelector('.sidebar-nav .selected a') ||
      document.querySelector('.sidebar-nav a.selected') ||
      document.querySelector('.sidebar-nav .sidebar-subheading');

    if (activeLink) {
      var mobileButtonText = activeLink.innerHTML;
    } else {
      var mobileButtonText = 'Sidebar';
    }

    button.innerHTML = mobileButtonText;
  }

  if (sidebarList && _mqWide.matches) {
    window.Mzp.Details.init('.details-heading');
    swapMobileSubnavText();
  }
  _mqWide.addListener(function(mq) {
    if (sidebarList && mq.matches) {
      window.Mzp.Details.init('.details-heading');
      swapMobileSubnavText();

    } else {
      window.Mzp.Details.destroy('.details-heading');
    }
  });

  // built for quote dropdowns in forum pages –
  // this is a global selector to always show dropdowns
  var forumDropdown = document.querySelector('[data-has-dropdown]');
  if ( forumDropdown ) {
    window.Mzp.Details.init('[data-has-dropdown]');
  }

  collapsibleAccordionInit();
}

detailsInit();
