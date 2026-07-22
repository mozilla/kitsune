import readerModeIcon from "protocol/img/icons/reader-mode.svg";
import blogIcon from "protocol/img/icons/blog.svg";
import detailsInit from "./protocol-details-init";
import tabsInit from "./sumo-tabs";
import trackEvent, { addGAEventListeners } from "sumo/js/analytics";
import Search from "sumo/js/search_utils";
import { toElements } from "sumo/js/utils/dom";

import "sumo/tpl/macros.njk";
import "sumo/tpl/search-results-list.njk";
import "sumo/tpl/search-results.njk";
import nunjucksEnv from "sumo/js/nunjucks"; // has to be loaded after templates

var searchTimeout;
var locale = document.documentElement.lang;
const searchTitle = "Search | Mozilla Support";

var search = new Search("/" + locale + "/search/");

var aaq_explore_step = document.getElementById("question-search-masthead") !== null;

const queries = [];
let renderedQuery;

// Show/hide via the CSSOM display setter, matching jQuery's .hide()/.show().
// (Inline display set through the CSSOM is not governed by CSP style-src.)
function hide(target) {
  toElements(target).forEach(function (el) {
    el.style.display = "none";
  });
}

function show(target) {
  toElements(target).forEach(function (el) {
    el.style.display = "";
  });
}

// The <aside> siblings of an element, mirroring jQuery's .siblings('aside').
function siblingAsides(el) {
  if (!el || !el.parentNode) {
    return [];
  }
  return Array.from(el.parentNode.children).filter(function (child) {
    return child !== el && child.matches("aside");
  });
}

function focusFirst(selector) {
  var el = document.querySelector(selector);
  if (el) {
    el.focus();
  }
}

function hideContent() {
  var mainContent = document.getElementById("main-content");
  if (mainContent) {
    mainContent.style.display = "none";
    siblingAsides(mainContent).forEach(function (el) {
      el.style.display = "none";
    });
  }
  document.body.classList.add("search-results-visible");
  document.querySelectorAll(".home-search-section .mzp-l-content").forEach(function (el) {
    el.classList.remove("narrow");
  });
  document.querySelectorAll(".home-search-section").forEach(function (el) {
    el.classList.remove("extra-pad-bottom");
  });

  // If applicable, close the mobile search field and move the focus to the main field.
  document.querySelectorAll(".sumo-nav--mobile-search-form").forEach(function (el) {
    el.classList.remove("mzp-is-open");
    el.setAttribute("aria-expanded", "false");
  });

  if (aaq_explore_step) {
    // in aaq explore step we don't want any search to show the default masthead
    hide(".hidden-search-masthead");
    show(".question-masthead");
    document.querySelectorAll(".page-heading--logo").forEach(function (el) {
      el.style.display = "block";
    });
  } else {
    show(".hidden-search-masthead");
  }
}

function showContent() {
  document.body.classList.remove("search-results-visible");
  document.querySelectorAll(".home-search-section").forEach(function (el) {
    el.classList.add("extra-pad-bottom");
  });
  hide(".support-search-main");
  var mainContent = document.getElementById("main-content");
  if (mainContent) {
    mainContent.style.display = "";
    siblingAsides(mainContent).forEach(function (el) {
      el.style.display = "";
    });
  }
  var instantContent = document.getElementById("instant-search-content");
  if (instantContent) {
    instantContent.remove();
  }
  document.querySelectorAll('[data-instant-search="form"] input[name="q"]').forEach(function (el) {
    el.value = "";
  });
  show(".page-heading--intro-text");
  document.querySelectorAll(".home-search-section--content .search-results-heading").forEach(function (el) {
    el.remove();
  });
  document.querySelectorAll(".home-search-section .mzp-l-content").forEach(function (el) {
    el.classList.add("narrow");
  });
  hide(".hidden-search-masthead");
}

function render(data) {
  var context = Object.assign({
    icons: {
      reader_mode: readerModeIcon,
      blog: blogIcon,
    },
  }, data);

  let query = context.q;
  if (queries.lastIndexOf(query) < queries.lastIndexOf(renderedQuery)) {
    // this query was sent before the query already rendered, don't render it
    return;
  }
  renderedQuery = query;

  let historyState = {
    query,
    params: search.params
  }
  if (history.state?.query) {
    // if a search is already the latest point in history, replace it
    // to avoid filling history with partial searches
    history.replaceState(historyState, searchTitle, "#search");
  } else {
    history.pushState(historyState, searchTitle, "#search");
  }

  context.base_url = search.lastQueryUrl();

  var searchContent = document.getElementById("instant-search-content");
  if (!searchContent) {
    searchContent = document.createElement("div");
    searchContent.id = "instant-search-content";
    var mainContent = document.getElementById("main-content");
    if (mainContent) {
      mainContent.after(searchContent);
    }
  }

  searchContent.innerHTML = nunjucksEnv.render("search-results.njk", context);
  if (aaq_explore_step) {
    searchContent.querySelectorAll("section a").forEach(function (a) {
      a.setAttribute("target", "_blank");
    });
  }

  addGAEventListeners("#instant-search-content");
  detailsInit(); // fold up sidebar on mobile.
  tabsInit();

  // hide intro text when showing search results
  hide(".page-heading--intro-text");

  // change aaq link if we're in aaq flow
  if (aaq_explore_step) {
    // Extract product slug from current URL path
    var pathParts = window.location.pathname.split('/').filter(function (part) {
      return part.length > 0;
    });
    // Look for the pattern /questions/new/{product_slug}
    var questionsIndex = pathParts.indexOf('questions');
    var newIndex = pathParts.indexOf('new');
    if (questionsIndex !== -1 && newIndex !== -1 && newIndex === questionsIndex + 1 && newIndex + 1 < pathParts.length) {
      var productSlug = pathParts[newIndex + 1];
      if (productSlug && productSlug !== 'form') {
        var aaqLink = document.getElementById("search-results-aaq-link");
        if (aaqLink) {
          aaqLink.setAttribute("href", "/questions/new/" + productSlug + "/form");
        }
      }
    }
  }
}

function getSearchProductFilter() {
  return search.getParam("product") || "";
}

function getSearchContentFilter() {
  switch (search.getParam("w")) {
    case "1":
      return "wiki";
    case "2":
      return "aaq";
    default:
      return "all-results";
  }
}

const InstantSearchSettings = {
  hideContent: hideContent,
  showContent: showContent,
  render: render,
  searchClient: search
};

document.addEventListener('submit', function (ev) {
  var form = ev.target.closest('[data-instant-search="form"]');
  if (!form) {
    return;
  }
  ev.preventDefault();
  var box = form.querySelector('.searchbox');
  if (box) {
    box.focus();
  }
});

document.addEventListener('input', function (ev) {
  var input = ev.target;
  if (!input.matches || !input.matches('[data-instant-search="form"] input[type="search"]')) {
    return;
  }
  var form = input.closest('form');
  var formId = form ? form.getAttribute('id') : null;
  var params = {
    format: 'json'
  };

  if (input.value.length === 0) {
    if (searchTimeout) {
      window.clearTimeout(searchTimeout);
    }

    InstantSearchSettings.showContent();

    if (history.state?.query) {
      history.pushState({}, searchTitle, location.href.replace("#search", ""));
    }
  } else if (input.value !== search.lastQuery) {
    if (searchTimeout) {
      window.clearTimeout(searchTimeout);
    }

    InstantSearchSettings.hideContent();

    form.querySelectorAll('input').forEach(function (el) {
      var type = el.getAttribute('type');
      if (type === 'submit' || type === 'button') {
        return;
      }
      if (el.getAttribute('name') === 'q') {
        var value = el.value;
        // update the values in all search forms which aren't the one the user is typing into
        document.querySelectorAll('[data-instant-search="form"]').forEach(function (otherForm) {
          if (otherForm !== form) {
            otherForm.querySelectorAll('input[name="q"]').forEach(function (i) {
              i.value = value;
            });
          }
        });
        return;
      }
      params[el.getAttribute('name')] = el.value;
    });

    searchTimeout = setTimeout(function () {
      search.unsetParam("page");
      search.setParams(params);
      let query = input.value.trim();
      queries.push(query);
      search.query(query, InstantSearchSettings.render);
      trackEvent("search", {
        "search_term": query,
        "search_product_filter": getSearchProductFilter(),
        "search_content_filter": getSearchContentFilter()
      });
    }, 600);
  }

  if (formId === "support-search" || formId === "mobile-search-results") {
    window.scrollTo(0, 0);
  }

  if (aaq_explore_step) {
    focusFirst(".question-masthead input[name=q]");
  } else if (document.querySelector(".hidden-search-masthead")) {
    focusFirst(".hidden-search-masthead input[name=q]");
  } else {
    focusFirst("#support-search-masthead input[name=q]");
  }
});

document.addEventListener('click', function (ev) {
  var link = ev.target.closest('[data-instant-search="link"]');
  if (!link) {
    return;
  }
  ev.preventDefault();

  var setParams = link.dataset.instantSearchSetParams;
  if (setParams) {
    setParams.split('&').forEach(function (pair) {
      var p = pair.split('=');
      search.setParam(p.shift(), p.join('='));
    });
  }

  var unsetParams = link.dataset.instantSearchUnsetParams;
  if (unsetParams) {
    unsetParams.split('&').forEach(function (key) {
      search.unsetParam(key);
    });
  }

  search.query(null, InstantSearchSettings.render);
  trackEvent("search", {
    "search_term": search.lastQuery,
    "search_product_filter": getSearchProductFilter(),
    "search_content_filter": getSearchContentFilter()
  });

  // Scroll to top of the page
  window.scrollTo(0, 0);
});

// 'Popular searches' feature
document.addEventListener('click', function (ev) {
  var link = ev.target.closest('[data-featured-search]');
  if (!link) {
    return;
  }
  var mainInput = document.querySelector('#support-search-masthead input[name=q]');
  if (mainInput) {
    mainInput.focus();
    mainInput.value = link.textContent;
    mainInput.dispatchEvent(new Event('input', { bubbles: true }));
  }
  ev.preventDefault();
});

document.addEventListener('click', function (ev) {
  var button = ev.target.closest('[data-mobile-nav-search-button]');
  if (!button) {
    return;
  }
  // If we hijack the layout of the page and the user clicks the button again.
  // assume they want to get rid of the search.
  var hiddenMasthead = document.querySelector('.hidden-search-masthead');
  if (hiddenMasthead && hiddenMasthead.offsetParent !== null) {
    InstantSearchSettings.showContent();
  } else if (aaq_explore_step) {
    // in aaq explore step, we don't want to show the default masthead
    focusFirst('#question-search-masthead input[name=q]');
    window.scrollTo(0, 0);
  } else if (hiddenMasthead) {
    document.body.classList.add('search-results-visible');
    hiddenMasthead.style.display = "";
    focusFirst('.hidden-search-masthead input[name=q]');
    window.scrollTo(0, 0);
  } else {
    // catchall for pages with a searchbox in the masthead
    var box = document.querySelector('.simple-search-form .searchbox');
    if (box) {
      box.dispatchEvent(new Event('keyup', { bubbles: true }));
      box.focus();
    }
  }

  ev.preventDefault();
});

function loadFromHistory(e) {
  let state = e.type == "popstate" ? e.state : history.state;
  if (state?.query) {
    InstantSearchSettings.hideContent();
    document.querySelectorAll('[data-instant-search="form"] input[name="q"]').forEach(function (el) {
      el.value = state.query;
    });
    search.params = state.params;
    queries.push(state.query);
    search.query(state.query, InstantSearchSettings.render);
  } else {
    InstantSearchSettings.showContent();
  }
}

window.addEventListener("popstate", loadFromHistory);
window.addEventListener("DOMContentLoaded", loadFromHistory);
