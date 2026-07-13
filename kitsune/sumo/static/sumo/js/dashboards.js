import { apiFetch } from "sumo/js/utils/fetch";

function toggleDisplay(el) {
  if (window.getComputedStyle(el).display === "none") {
    el.style.display = "block";
  } else {
    el.style.display = "none";
  }
}

function init() {
  initReadoutModes();
  initWatchMenu();
  initNeedsChange();
  initL10nStringsStats();
  initLocalizationTabs();
  setProgressBarWidth();
}

// Hook up readout mode links (like "This Week" and "All Time") to swap
// table data.
function initReadoutModes() {
  document.querySelectorAll('.readout-modes').forEach(function (modes) {
    var slug = modes.getAttribute('data-slug');
    modes.querySelectorAll('.mode').forEach(function (button) {
      button.addEventListener('click', function (e) {
        e.preventDefault();
        // Dim table to convey that its data isn't what the selected mode
        // indicates:
        var table = document.getElementById(slug + '-table');
        if (table) {
          table.classList.add('busy');
        }

        // Update button appearance:
        modes.querySelectorAll('.mode').forEach(function (m) {
          m.classList.remove('active');
        });
        button.classList.add('active');

        apiFetch(button.getAttribute('data-url'), { dataType: 'html' }).then(function (html) {
          if (table) {
            table.innerHTML = html;
            table.classList.remove('busy');
          }
          setProgressBarWidth();
        });
      });
    });
  });
}

function initWatchMenu() {
  var watchDiv = document.getElementById('doc-watch');
  if (!watchDiv) {
    return;
  }
  var menu = watchDiv.querySelector('.popup-menu');

  // Initialize popup menu behavior:
  var trigger = watchDiv.querySelector('.popup-trigger');
  if (trigger && menu) {
    trigger.addEventListener('click', function () {
      toggleDisplay(menu);
    });
  }

  // Teach checkboxes to dim and post on click:
  // Dim the checkbox, post the watch change, then undim.
  watchDiv.querySelectorAll('input[type=checkbox]').forEach(function (box) {
    box.addEventListener('click', function () {
      var form = box.closest('form');
      var csrfEl = form ? form.querySelector('input[name=csrfmiddlewaretoken]') : null;
      var csrf = csrfEl ? csrfEl.value : '';
      var isChecked = box.checked;
      box.disabled = true;

      apiFetch(isChecked ? box.dataset.actionWatch : box.dataset.actionUnwatch, {
        method: 'POST',
        data: { csrfmiddlewaretoken: csrf },
      })
        .then(function () {
          box.disabled = false;
        })
        .catch(function () {
          // On error, revert the checked state and re-enable the checkbox.
          box.checked = !isChecked;
          box.disabled = false;
        });
    });
  });
}

function initNeedsChange() {
  // Expand rows on click
  document.querySelectorAll('#need-changes-table tr').forEach(function (row) {
    row.addEventListener('click', function (e) {
      // Don't expand if a link was clicked.
      if (!e.target.matches('a')) {
        row.classList.toggle('active');
      }
    });
  });
}

function initL10nStringsStats() {
  // Create the progress bar for UI string stats in the overview
  // section of the l10n dashboard.
  var tr = document.querySelector('tr.ui-strings-row');
  if (!tr) {
    return;
  }
  var tds = tr.querySelectorAll('td');
  var now = new Date();
  var cacheBust = now.getYear().toString() +
    now.getMonth().toString() +
    now.getDay().toString();

  apiFetch('/media/uploads/l10n_summary.json?_cache=' + cacheBust, { dataType: 'json' }).then(function (data) {
    var localeData = data.locales[document.documentElement.lang];
    if (!localeData) {
      return;
    }
    var className = 'bad';

    // Fill in the numbers in the second column.
    tds[1].innerHTML = interpolate(
      gettext('%(num)s <small>of %(total)s</small>'),
      {
        num: localeData.translated,
        total: localeData.total,
      },
      true
    );

    // Fill in the progress bar in the third column.
    if (localeData.percent >= 20) {
      className = 'better';
    }
    if (localeData.percent === 100) {
      className = 'best';
    }
    tds[2].innerHTML = interpolate(
      '%(percent)s% ' +
      '<div class="percent-graph">' +
      '<div style="width: %(percent)s%" class="%(className)s">' +
      '</div>' +
      '</div>',
      {
        percent: localeData.percent,
        className: className,
      },
      true
    );
  });
}

function setProgressBarWidth() {
  const graphBars = document.getElementsByClassName("absolute-graph");
  for (const bar of graphBars) {
    bar.style.width = bar.getAttribute("data-absolute-graph");
  }
}

function initLocalizationTabs() {
  const tabs = document.querySelectorAll('.dashboards nav.localization.tabs .tabs--link');
  const tabContents = document.querySelectorAll('.dashboards .localization.tabs--content');

  tabs.forEach(function (tab) {
    tab.addEventListener('click', function () {
      // Remove active class from all tabs and hide all tab contents
      tabs.forEach(function (tab) {
        tab.classList.remove('is-active');
      });

      tabContents.forEach(function (content) {
        content.classList.remove('is-active');
      });

      // Add active class to the selected tab and show its content
      tab.classList.add('is-active');
      const targetContent = document.getElementById('tab-' + tab.getAttribute('data-tab-content-id'));
      if (targetContent) {
        targetContent.classList.add('is-active');
      }

      window.location.hash = tab.id;
    });
  });

  if (window.location.hash.length > 1) {
    var target = null;
    try {
      target = document.querySelector(window.location.hash);
    } catch (e) {
      target = null;
    }
    if (target) {
      target.click();
    }
  }
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}
