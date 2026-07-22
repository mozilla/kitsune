import questionmarkIcon from "sumo/img/questions/icon.questionmark.png";
import _throttle from "underscore/modules/throttle";
import KBox from "sumo/js/kbox";
import AjaxPreview from "sumo/js/ajaxpreview";
import AjaxVote from "sumo/js/ajaxvote";
import { getQueryParamsAsDict, getReferrer, getSearchQuery, unquote } from "sumo/js/main";
import Marky from "sumo/js/markup";
import AAQSystemInfo from "sumo/js/aaq";
import { apiFetch } from "sumo/js/utils/fetch";
import { getCookie } from "sumo/js/utils/cookie";
import { serialize, slideToggle } from "sumo/js/utils/dom";

/*
* questions.js
* Scripts for the questions app.
*/

document.addEventListener("DOMContentLoaded", async () => {
  const body = document.querySelector("body.new-question");
  if (body) {
    const submitButton = body.querySelector('#question-form button[type="submit"]');
    if (submitButton) {
      body.addEventListener('setQuestionSubmitEventParameters', (event) => {
        submitButton.dataset.eventParameters = event.detail.eventParameters;
      });
    }
  }
});

// Put the last search query back into the answers-page search box.
export function restoreLastSearchQuery() {
  var searchBox = document.querySelector('#support-search input[name=q]');
  if (searchBox) {
    // Default to "" - getCookie returns undefined when the cookie is missing,
    // and assigning that to .value would show the literal string "undefined".
    searchBox.value = unquote(getCookie('last_search')) || '';
  }
}

function init() {
  var body = document.body;

  // if there's an error on page load, focus the field.
  var errorField = document.querySelector('.has-error input, .has-error textarea');
  if (errorField) {
    errorField.focus();
  }

  if (body.classList.contains('new-question')) {
    initQuestion();
  }

  if (body.classList.contains('edit-question')) {
    initQuestion("editing");
  }

  if (body.classList.contains('questions')) {
    initTagFilterToggle();

    document.querySelectorAll('#flag-filter input[type="checkbox"]').forEach(function (cb) {
      cb.addEventListener('click', function () {
        window.location = cb.dataset.url;
      });
    });
  }

  if (body.classList.contains('answers')) {
    restoreLastSearchQuery();

    var content = document.getElementById('id_content');
    if (content) {
      content.addEventListener('keyup', _throttle(takeQuestion, 60000));
    }

    document.addEventListener('click', function (ev) {
      if (ev.target.closest('#details-edit')) {
        ev.preventDefault();
        var details = document.getElementById('question-details');
        if (details) {
          details.classList.add('editing');
        }
      } else if (ev.target.closest('#details-cancel')) {
        ev.preventDefault();
        var form = ev.target.closest('#details-cancel').closest('form');
        if (form) {
          form.reset();
        }
        var detailsToClose = document.getElementById('question-details');
        if (detailsToClose) {
          detailsToClose.classList.remove('editing');
        }
      }
    });

    initHaveThisProblemTooAjax();
    initHelpfulVote();
    initCrashIdLinking();
    initEditDetails();
    addReferrerAndQueryToVoteForm();
    initReplyToAnswer();
    new AjaxPreview(document.getElementById('preview'));
  }

  Marky.createSimpleToolbar('.editor-tools', '#reply-content, #id_content', {
    cannedResponses: !body.classList.contains('new-question') && !body.classList.contains('edit-question'),
  });

  // product selector page reloading
  var productSelect = document.querySelector('#product-selector select');
  if (productSelect) {
    productSelect.addEventListener('change', function () {
      var val = productSelect.value;
      var queryParams = getQueryParamsAsDict(document.location.toString());

      if (val === '') {
        delete queryParams.product;
      } else {
        queryParams.product = val;
      }
      document.location = document.location.pathname + '?' + new URLSearchParams(queryParams).toString();
    });
  }
}

// Take (assign) a question to the current user once they start replying.
// Bound as a throttled keyup handler, so `this` is the content textarea.
function takeQuestion() {
  if (this.value.length > 0) {
    var form = this.closest('form');
    var url = form ? form.dataset.takeQuestionUrl : null;
    if (url) {
      // apiFetch adds the X-CSRFToken header automatically.
      apiFetch(url, { method: 'POST' });
    }
  }
}

/*
* Initialize the new/edit question page/form
*/
function initQuestion(action) {
  const questionForm = document.querySelector('#question-form');
  if (!questionForm) return;
  let aaq = new AAQSystemInfo(questionForm);
  if (action === "editing") {
    let troubleshootingField = questionForm.querySelector("#troubleshooting-field");
    if (troubleshootingField) {
      troubleshootingField.style.display = "block";
    }
  } else {
    aaq.fillDetails();
    hideDetails(questionForm);
  }
}

// Handle changes to the details for a question
export function initEditDetails() {
  var product = document.getElementById('details-product');
  if (!product) {
    return;
  }
  product.addEventListener('change', function () {
    var selected = product.selectedOptions[0];
    var topic = document.getElementById('details-topic');
    var submit = document.getElementById('details-submit');

    if (topic) {
      topic.innerHTML = '';
    }
    if (submit) {
      submit.disabled = true;
    }

    apiFetch(selected.dataset.url, { dataType: 'json' }).then(function (data) {
      for (var i = 0; i < data.topics.length; i++) {
        var t = data.topics[i];
        var opt = document.createElement('option');
        opt.value = t.id;
        // Titles arrive with &nbsp; entities for nested-topic indentation (built
        // server-side in get_hierarchical_topics). Render as HTML so the
        // entities decode to non-breaking spaces, matching the server-rendered
        // dropdowns which output the same title via `{{ title|safe }}`.
        opt.innerHTML = t.title;
        if (topic) {
          topic.appendChild(opt);
        }
      }
      if (submit) {
        submit.disabled = false;
      }
    });
  });
}

// Hide the browser/system details for users on FF with js enabled
// and are submitting a question for FF on desktop.
function hideDetails(form) {
  form.querySelector('ul').classList.add('hide-details');
  for (const link of form.querySelectorAll('a.show, a.hide')) {
    link.addEventListener("click", e => {
      e.preventDefault();
      const li = e.currentTarget.closest("li");
      li.classList.toggle("show");
      li.classList.toggle("hide");
      const ui = li.closest("ul");
      ui.classList.toggle("show-details");
    });
  }
}

/*
* Ajaxify any "I have this problem too" forms (may be multiple per page)
*/
function initHaveThisProblemTooAjax() {
  var containers = document.querySelectorAll('#question div.me-too, .question-tools div.me-too');

  containers.forEach(function (container) {
    // ajaxify each form individually so the resulting kbox attaches to
    // the correct DOM element
    initAjaxForm(container, 'form', '#vote-thanks');

    container.querySelectorAll('input').forEach(function (input) {
      input.addEventListener('click', function () {
        input.setAttribute('disabled', 'disabled');
      });
    });

    // closing or cancelling the kbox on any of the forms should remove
    // all of them
    container.addEventListener('click', function (ev) {
      if (ev.target.closest('.kbox-close, .kbox-cancel')) {
        ev.preventDefault();
        containers.forEach(function (c) {
          c.remove();
        });
      }
    });
  });
}

function addReferrerAndQueryToVoteForm() {
  // Add the source/referrer and query terms to the helpful vote form
  var urlParams = getQueryParamsAsDict();
  var referrer = getReferrer(urlParams);
  var query = getSearchQuery(urlParams, referrer);
  document.querySelectorAll('form.helpful, .me-too form').forEach(function (form) {
    var referrerInput = document.createElement('input');
    referrerInput.type = 'hidden';
    referrerInput.name = 'referrer';
    referrerInput.value = referrer;
    form.appendChild(referrerInput);

    var queryInput = document.createElement('input');
    queryInput.type = 'hidden';
    queryInput.name = 'query';
    queryInput.value = query;
    form.appendChild(queryInput);
  });
}

/*
* Ajaxify the Helpful/Not Helpful form
*/
function initHelpfulVote() {
  document.querySelectorAll('.sumo-l-two-col--sidebar, #document-list, .answer-footer').forEach(function (el) {
    new AjaxVote(el.querySelector('form.helpful'), {
      replaceFormWithMessage: true,
      removeForm: true,
    });
  });
}

// Helper
function initAjaxForm(container, formSelector, boxSelector, onKboxClose) {
  container.addEventListener('submit', function (ev) {
    var form = ev.target.closest(formSelector);
    if (!form || !container.contains(form)) {
      return;
    }
    ev.preventDefault();
    var url = form.getAttribute('action');

    apiFetch(url, { method: 'POST', data: serialize(form), dataType: 'json' })
      .then(function (response) {
        if (response.html) {
          var box = document.querySelector(boxSelector);
          if (!box) {
            // We don't have a modal set up yet.
            var kbox = new KBox(response.html, {
              container: container,
              preClose: onKboxClose,
            });
            kbox.open();
          } else {
            // Replace the box contents with the children of the returned markup
            // (mirrors the old jQuery `.html($(response.html).children())`).
            var temp = document.createElement('div');
            temp.innerHTML = response.html;
            var children = [];
            Array.from(temp.children).forEach(function (topEl) {
              children.push.apply(children, Array.from(topEl.children));
            });
            box.replaceChildren.apply(box, children);
          }
        } else if (response.message) {
          var submit = form.querySelector('[type="submit"]');
          if (submit) {
            submit.disabled = true;
          }
          var existing = form.parentNode.querySelector('.vote-rate-limit-msg');
          if (existing) {
            existing.remove();
          }
          var msg = document.createElement('p');
          msg.className = 'vote-rate-limit-msg';
          msg.textContent = response.message;
          form.insertAdjacentElement('afterend', msg);
        }

        if (!response.ignored) {
          // Trigger an event for others to listen for.
          document.dispatchEvent(new CustomEvent("vote-for-question", { bubbles: true, detail: { url: url } }));
        }
      })
      .catch(function () {
        var message = gettext('There was an error.');
        alert(message);
      });
  });
}

function initTagFilterToggle() {
  var toggle = document.getElementById('toggle-tag-filter');
  if (!toggle) {
    return;
  }
  toggle.addEventListener("click", function (e) {
    e.preventDefault();
    var filter = document.getElementById('tag-filter');
    if (filter) {
      slideToggle(filter); // CSS3: Y U NO TRANSITION TO `height: auto;`?
    }
    toggle.classList.toggle('off');
  });
}

/*
* Links all crash IDs found in the passed HTML container element
*/
export function linkCrashIds(container) {
  if (!container) {
    return;
  }
  var crashIDRegex = new RegExp('(bp-[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})', 'g');
  var crashStatsBase = 'https://crash-stats.mozilla.org/report/index/';
  var helpingWithCrashesArticle = '/kb/helping-crashes';
  var crashReportContainer =
  "<span class='crash-report'>" +
  "<a href='" + crashStatsBase + "$1' target='_blank'>$1</a>" +
  "<a href='" + helpingWithCrashesArticle + "' target='_blank'>" +
  "<img src='" + questionmarkIcon + "'></img></a></span>";

  container.innerHTML = container.innerHTML.replace(crashIDRegex, crashReportContainer);
}

/*
* Initialize the automatic linking of crash IDs
*/
function initCrashIdLinking() {
  document.querySelectorAll('.question .content, .answer .main-content, #more-system-details').forEach(function (el) {
    linkCrashIds(el);
  });
}

function initReplyToAnswer() {
  document.querySelectorAll('a.quoted-reply').forEach(function (link) {
    link.addEventListener("click", function () {
      var contentId = link.dataset.contentId;
      var contentEl = document.getElementById(contentId);
      var rawEl = contentEl ? contentEl.querySelector('.content-raw') : null;
      var nameEl = contentEl ? contentEl.querySelector('.display-name') : null;
      var text = rawEl ? rawEl.textContent : '';
      var user = nameEl ? nameEl.textContent : '';
      var reply_text = `''<p>${user} [[#${contentId}|${gettext('said')}]]</p>''\n<blockquote>${text}\n</blockquote>\n\n`;
      var textarea = document.getElementById('id_content');

      if (textarea) {
        textarea.value = textarea.value + reply_text;
        setTimeout(function () {
          textarea.focus();
        }, 10);
      }

      return true;
    });
  });
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}

const TAGS_INITIAL_LIMIT = 10;
const TAGS_PAGE_SIZE = 20;
const TAGS_MAX_LIMIT = 50;

function initSidebarTagFilter() {
  const container = document.querySelector("#sidebar-tag-filter");
  if (!container || container.dataset.initialized) return;

  const searchInput = container.querySelector(".sidebar-tags--search");
  const noResults = container.querySelector(".sidebar-tags--no-results");
  const showMoreBtn = container.querySelector(".sidebar-tags--show-more");
  const tagList = container.querySelector(".sidebar-tags--list");
  let tagItems = container.querySelectorAll(".sidebar-tags--list li");
  let total = tagItems.length;

  // Content not loaded yet (HTMX hasn't fired) — don't mark as initialized
  if (!total) return;
  container.dataset.initialized = "true";
  let maxLimit = Math.min(total, TAGS_MAX_LIMIT);
  let limit = TAGS_INITIAL_LIMIT;
  const initialLimit = limit;

  const originalListHTML = tagList ? tagList.innerHTML : "";
  let isServerRendered = false;
  let fallbackTimer = null;
  let fallbackController = null;

  function refreshTagItems() {
    tagItems = container.querySelectorAll(".sidebar-tags--list li");
    total = tagItems.length;
    maxLimit = Math.min(total, TAGS_MAX_LIMIT);
  }

  function restoreOriginal() {
    if (!isServerRendered || !tagList) return;
    tagList.innerHTML = originalListHTML;
    refreshTagItems();
    isServerRendered = false;
  }

  function updateVisibility() {
    const query = searchInput ? searchInput.value.toLowerCase() : "";
    const searching = query.length > 0;
    let visibleCount = 0;

    if (isServerRendered) {
      tagItems.forEach(li => {
        li.classList.remove("is-hidden");
        visibleCount++;
      });
    } else {
      tagItems.forEach(li => {
        const show = searching ? (li.dataset.name || "").includes(query) : parseInt(li.dataset.rank, 10) < limit;
        li.classList.toggle("is-hidden", !show);
        if (show) visibleCount++;
      });
    }

    if (noResults) {
      noResults.hidden = !(searching && visibleCount === 0);
    }

    if (showMoreBtn) {
      const shouldHide = searching || isServerRendered || (total <= initialLimit);
      showMoreBtn.hidden = shouldHide;
      if (shouldHide) {
        showMoreBtn.classList.remove("is-expanded");
      } else {
        const expanded = limit >= maxLimit;
        showMoreBtn.classList.toggle("is-expanded", expanded);
        const textSpan = showMoreBtn.querySelector("span");
        if (textSpan) {
          if (expanded) {
            textSpan.textContent = interpolate(
              ngettext("Hide %(n)s tag", "Hide %(n)s tags", maxLimit - initialLimit),
              { n: maxLimit - initialLimit },
              true
            );
          } else {
            const next = Math.min(limit + TAGS_PAGE_SIZE, maxLimit);
            textSpan.textContent = interpolate(
              ngettext("Show %(n)s more tag", "Show %(n)s more tags", next - limit),
              { n: next - limit },
              true
            );
          }
        }
      }
    }

    return { searching, query, visibleCount };
  }

  function fetchFallback(query) {
    if (!tagList) return;

    if (fallbackController) fallbackController.abort();
    fallbackController = new AbortController();

    const hxUrl = container.getAttribute("hx-get") || "";
    if (!hxUrl) return;
    const url = new URL(hxUrl, window.location.origin);
    url.searchParams.set("q", query);

    fetch(url.toString(), { signal: fallbackController.signal })
      .then(r => r.ok ? r.text() : Promise.reject(r))
      .then(html => {
        const doc = new DOMParser().parseFromString(html, "text/html");
        const newList = doc.querySelector(".sidebar-tags--list");
        tagList.innerHTML = newList ? newList.innerHTML : "";
        refreshTagItems();
        isServerRendered = true;
        updateVisibility();
      })
      .catch(err => {
        if (err && err.name === "AbortError") return;
      });
  }

  function onInput() {
    if (fallbackTimer) {
      clearTimeout(fallbackTimer);
      fallbackTimer = null;
    }
    if (isServerRendered) {
      restoreOriginal();
    }

    const { searching, query, visibleCount } = updateVisibility();

    if (!searching) {
      if (fallbackController) {
        fallbackController.abort();
        fallbackController = null;
      }
      return;
    }

    if (visibleCount === 0) {
      fallbackTimer = setTimeout(() => fetchFallback(query), 250);
    }
  }

  if (searchInput) {
    searchInput.addEventListener("input", onInput);
  }

  if (showMoreBtn) {
    showMoreBtn.addEventListener("click", () => {
      if (isServerRendered) return;
      limit = limit >= maxLimit ? initialLimit : Math.min(limit + TAGS_PAGE_SIZE, maxLimit);
      updateVisibility();
    });
  }

  updateVisibility();
}

document.addEventListener("DOMContentLoaded", initSidebarTagFilter);
document.addEventListener("htmx:afterSettle", (event) => {
  const sidebar = document.getElementById("sidebar-tag-filter");
  if (sidebar && event.detail && event.detail.target === sidebar) {
    delete sidebar.dataset.initialized;
  }
  initSidebarTagFilter();
});

// Delegated change listener for question-list dropdowns. Each <option value>
// is a full URL. Delegated on document so listeners survive the oob swap that
// replaces these <select>s when other filters change.
//  - Topic dropdown: htmx.ajax reads target/select/swap/oob/push-url from the
//    <select> itself via the source option.
//  - Sort dropdown(s): full page reload to keep existing behavior.
document.addEventListener("change", (event) => {
  const select = event.target;
  if (!select) return;
  const url = select.value;
  if (!url) return;
  if (select.id === "products-topics-dropdown") {
    htmx.ajax("GET", url, { source: select });
  } else if (select.matches && select.matches("[data-sort-questions]")) {
    document.location = url;
  }
});
