import "sumo/js/protocol";
import Details from "protocol/js/details";


export function collapsibleAccordionInit() {
  'use strict';
  // Initialize any header elements, or header elements wrapped by a "div.for"
  // element (which is generated from the Wiki syntax "{for ...}{/for}") that
  // are direct children of an element with the "mzp-c-details" class.
  for (let hdr of ['h2', 'h3', 'h4', 'h5', 'h6']) {
    Details.init(`.mzp-c-details > ${hdr}, .mzp-c-details > div.for > ${hdr}`);
  }
}

export default function detailsInit() {
  'use strict';
  var _mqWide = matchMedia('(max-width: 1055px)');

  function swapMobileSubnavText(heading) {
    var button = heading.querySelector('button');
    if (!button) {
      return;
    }
    var sidebar = heading.closest('.sidebar-nav') || heading.parentNode;
    var activeLink = sidebar.querySelector('.selected a') ||
      sidebar.querySelector('a.selected') ||
      sidebar.querySelector('select option:checked') ||
      sidebar.querySelector('.sidebar-subheading');

    button.innerHTML = activeLink ? activeLink.innerHTML : 'Sidebar';
  }

  function initializeMobileDetails() {
    var sidebarHeadings = document.querySelectorAll('.details-heading');
    if (!sidebarHeadings.length) {
      return;
    }
    Details.init('.details-heading');
    var aside = document.querySelector('#aside');
    var hideAside = aside && document.body.classList.contains('document')
      && (document.querySelector('#doc-tools')?.textContent ?? "").trim() === "";
    if (hideAside) {
      // The only potential section of a mobile article sidebar is empty, so there's no sense in displaying the sidebar.
      // This isn't relevant for the large version, where the sidebar will always include the helpfulness survey at least.
      // Note that we can't check #aside directly, since the helpfulness survey has not been moved from it yet.
      aside.hidden = true;
    }
    sidebarHeadings.forEach(function(heading) {
      if (!(hideAside && aside.contains(heading))) {
        swapMobileSubnavText(heading);
      }
    });
  }

  if (_mqWide.matches) {
    initializeMobileDetails();
  }
  _mqWide.addListener(function(mq) {
    if (mq.matches) {
      initializeMobileDetails();
    } else {
      Details.destroy('.details-heading');
      let aside = document.querySelector('#aside');
      if (aside) {
        aside.hidden = false;
      }
    }
  });

  // built for quote dropdowns in forum pages –
  // this is a global selector to always show dropdowns
  var forumDropdown = document.querySelector('[data-has-dropdown]');
  if ( forumDropdown ) {
    Details.init('[data-has-dropdown]');
  }

  collapsibleAccordionInit();
}

detailsInit();
