import _throttle from "underscore/modules/throttle";
import UITour from "./libs/uitour";
import trackEvent from "sumo/js/analytics";

// Show/hide mirroring jQuery's .show()/.hide(): several targets here are hidden
// by a CSS rule (announce bars, data-close-initial="hidden" targets, tab
// panels), so reveal them by forcing a display when a stylesheet still hides.
function show(el) {
  if (!el) {
    return;
  }
  el.hidden = false;
  el.style.display = "";
  if (window.getComputedStyle(el).display === "none") {
    el.style.display = "block";
  }
}

function hide(el) {
  if (el) {
    el.style.display = "none";
  }
}

function submitForm(form) {
  if (!form) {
    return;
  }
  if (form.requestSubmit) {
    form.requestSubmit();
  } else {
    form.submit();
  }
}

function ready() {
  initFolding();
  initAnnouncements();

  var deleteInput = document.getElementById('delete-profile-confirmation-input');
  if (deleteInput) {
    deleteInput.addEventListener('keyup', function () {
      var confirmationEl = document.getElementById('delete-profile-confirmation');
      var confirmation = confirmationEl ? confirmationEl.value.trim() : '';
      var inputConfirmation = deleteInput.value.trim();
      var button = document.getElementById('delete-profile-button');
      if (button) {
        button.disabled = inputConfirmation !== confirmation;
      }
    });
  }

  window.addEventListener('scroll', _throttle(function () {
    var header = document.querySelector('body > header');
    var headerHeight = header ? header.offsetHeight : 0;
    if (window.scrollY > headerHeight) {
      document.body.classList.add('scroll-header');
    } else {
      document.body.classList.remove('scroll-header');
    }
  }, 100));

  document.addEventListener('click', function (ev) {
    var link = ev.target.closest('.ui-truncatable .show-more-link');
    if (!link) {
      return;
    }
    ev.preventDefault();
    var truncatable = link.closest('.ui-truncatable');
    if (truncatable) {
      truncatable.classList.remove('truncated');
    }
  });

  document.addEventListener('click', function (ev) {
    var btn = ev.target.closest('.close-button');
    if (!btn) {
      return;
    }
    var target;
    if (btn.dataset.closeId) {
      target = document.getElementById(btn.dataset.closeId);
      if (btn.dataset.closeMemory === 'remember') {
        localStorage.setItem(btn.dataset.closeId + '.closed', true);
      } else if (btn.dataset.closeMemory === 'session') {
        sessionStorage.setItem(btn.dataset.closeId + '.closed', true);
      }
    } else {
      target = btn.parentElement;
    }
    if (target) {
      if (btn.dataset.closeType === 'remove') {
        target.remove();
      } else {
        hide(target);
      }
    }
  });

  document.addEventListener('change', function (ev) {
    var select = ev.target.closest('select[data-submit]');
    if (!select) {
      return;
    }
    var form = select.dataset.submit ? document.getElementById(select.dataset.submit) : select.closest('form');
    submitForm(form);
  });

  document.querySelectorAll('[data-close-memory="remember"]').forEach(function (el) {
    var id = el.dataset.closeId;
    if (!id) {
      return;
    }
    var target = document.getElementById(id);
    if (!target) {
      return;
    }
    if (localStorage.getItem(id + '.closed') === 'true') {
      if (el.dataset.closeType === 'remove') {
        target.remove();
      } else {
        hide(target);
      }
    } else if (target.dataset.closeInitial === 'hidden') {
      show(target);
    }
  });

  document.querySelectorAll('[data-close-memory="session"]').forEach(function (el) {
    var id = el.dataset.closeId;
    if (!id) {
      return;
    }
    var target = document.getElementById(id);
    if (target && target.dataset.closeInitial === 'hidden' && sessionStorage.getItem(id + '.closed') !== 'true') {
      show(target);
    }
  });

  document.querySelectorAll('[data-toggle]').forEach(function (el) {
    var target = el.dataset.toggleTarget ? document.querySelector(el.dataset.toggleTarget) : el;
    var trigger = el.dataset.toggleTrigger || 'click';
    var targetId = target ? target.id : null;

    if (el.dataset.toggleSticky && targetId) {
      var stored = JSON.parse(localStorage.getItem(targetId + '.classes') || '[]');
      stored.forEach(function (cls) {
        if (cls) {
          target.classList.add(cls);
        }
      });
    }

    el.addEventListener(trigger, function (ev) {
      ev.preventDefault();
      var classname = el.dataset.toggle;
      if (target) {
        target.classList.toggle(classname);
      }

      if (el.dataset.toggleSticky && targetId) {
        var classes = JSON.parse(localStorage.getItem(targetId + '.classes') || '[]');
        var i = classes.indexOf(classname);

        if (target.classList.contains(classname) && i === -1) {
          classes.push(classname);
        } else if (!target.classList.contains(classname) && i > -1) {
          classes.splice(i, 1);
        }

        localStorage.setItem(targetId + '.classes', JSON.stringify(classes));
      }
    });
  });

  document.querySelectorAll('[data-ui-type="tabbed-view"]').forEach(function (tv) {
    var tabsContainer = tv.querySelector(':scope > [data-tab-role="tabs"]');
    var panelsContainer = tv.querySelector(':scope > [data-tab-role="panels"]');
    var tabs = [];
    if (tabsContainer) {
      // Mirrors $tv.children('[data-tab-role="tabs"]').children().children()
      Array.from(tabsContainer.children).forEach(function (child) {
        tabs.push.apply(tabs, Array.from(child.children));
      });
    }
    var panels = panelsContainer ? Array.from(panelsContainer.children) : [];

    tabs.forEach(function (tab, i) {
      tab.addEventListener('click', function (e) {
        e.preventDefault();
        panels.forEach(hide);
        if (panels[i]) {
          show(panels[i]);
        }
        tabs.forEach(function (t) {
          t.classList.remove('selected');
        });
        tab.classList.add('selected');
      });
    });

    if (tabs[0]) {
      tabs[0].click();
    }
  });

  document.querySelectorAll('.btn, .button, a').forEach(function (el) {
    var form = el.closest('form');
    var type = el.getAttribute('data-type');
    var trigger = el.getAttribute('data-trigger');

    if (type === 'submit') {
      // Clicking the element will submit a form.
      if (el.getAttribute('data-form')) {
        form = document.getElementById(el.getAttribute('data-form'));
      }

      el.addEventListener('click', function (ev) {
        var name = el.getAttribute('data-name');
        var value = el.getAttribute('data-value');

        ev.preventDefault();

        if (name && form) {
          var input = document.createElement('input');
          input.type = 'hidden';
          input.name = name;
          input.value = value ? value : '1';
          form.appendChild(input);
        }

        if (el.getAttribute('data-nosubmit') !== '1') {
          submitForm(form);
        }
      });
    } else if (trigger === 'click') {
      // Trigger a click on another element.
      el.addEventListener('click', function (ev) {
        ev.preventDefault();
        var targetSel = el.getAttribute('data-trigger-target');
        var target = targetSel ? document.querySelector(targetSel) : null;
        if (target) {
          target.click();
        }
      });
    }
  });

  var foldingSelectors = '.folding-section, [data-ui-type="folding-section"]';

  document.body.addEventListener('click', function (ev) {
    var header = ev.target.closest(foldingSelectors + ' header');
    if (!header) {
      return;
    }
    var section = header.closest(foldingSelectors);
    if (section) {
      section.classList.toggle('collapsed');
    }
  });

  document.querySelectorAll('form[data-confirm]').forEach(function (form) {
    form.addEventListener('submit', function (e) {
      if (!confirm(form.dataset.confirmText)) {
        e.preventDefault();
      }
    });
  });
}

window.addEventListener('load', function () {
  document.querySelectorAll('[data-ui-type="carousel"]').forEach(function (carousel) {
    var container = carousel.children[0];
    if (!container) {
      return;
    }

    var width = 0;
    var height = 0;

    Array.from(container.children).forEach(function (child) {
      if (height < child.offsetHeight) {
        height = child.offsetHeight;
      }
      var style = window.getComputedStyle(child);
      width += child.offsetWidth + parseInt(style.marginRight, 10) + parseInt(style.marginLeft, 10);
    });

    carousel.style.height = height + 'px';
    container.style.width = width + 'px';
    container.style.height = height + 'px';
    Array.from(container.children).forEach(function (child) {
      child.style.height = height + 'px';
    });

    var left = document.getElementById(carousel.dataset.left);
    var right = document.getElementById(carousel.dataset.right);
    var scrollInterval;

    if (left) {
      left.addEventListener('mouseover', function () {
        scrollInterval = setInterval(function () {
          carousel.scrollLeft = carousel.scrollLeft - 1;
        }, 1);
      });
      left.addEventListener('mouseout', function () {
        clearInterval(scrollInterval);
      });
    }

    if (right) {
      right.addEventListener('mouseover', function () {
        scrollInterval = setInterval(function () {
          carousel.scrollLeft = carousel.scrollLeft + 1;
        }, 1);
      });
      right.addEventListener('mouseout', function () {
        clearInterval(scrollInterval);
      });
    }
  });
});

function initFolding() {
  var folders = document.querySelectorAll('.sidebar-folding > li');
  // When a header is clicked, expand/contract the menu items.
  folders.forEach(function (folder) {
    folder.querySelectorAll(':scope > a, :scope > span').forEach(function (trigger) {
      trigger.addEventListener('click', function (ev) {
        ev.preventDefault();
        var parent = trigger.parentElement;
        parent.classList.toggle('selected');
        // Store this for future page loads.
        var id = parent.id;
        var folded = parent.classList.contains('selected');
        if (id) {
          localStorage.setItem(id + '.folded', folded);
        }
      });
    });
  });

  // Load the folded/unfolded state of the menus from local storage and apply it.
  folders.forEach(function (folder) {
    var id = folder.id;
    if (id) {
      var folded = localStorage.getItem(id + '.folded');
      if (folded === 'true') {
        folder.classList.add('selected');
      } else if (folded === 'false') {
        folder.classList.remove('selected');
      }
    }
  });
}

function initAnnouncements() {
  var announcements = document.getElementById('announcements');
  if (!announcements) {
    return;
  }

  // When an announcement is closed, remember it.
  announcements.addEventListener('click', function (ev) {
    var closeBtn = ev.target.closest('.close-button');
    if (!closeBtn || !announcements.contains(closeBtn)) {
      return;
    }
    var bar = closeBtn.closest('.announce-bar');
    if (bar && bar.id) {
      localStorage.setItem(bar.id + '.closed', true);
    }
  });

  // If an announcement has not been hidden before, show it.
  announcements.querySelectorAll('.announce-bar').forEach(function (bar) {
    var id = bar.id;
    if (localStorage.getItem(id + '.closed') !== 'true') {
      show(bar);
    }
  });
}

document.addEventListener('click', function (ev) {
  var toggle = ev.target.closest('#show-password');
  if (!toggle) {
    return;
  }
  var form = toggle.closest('form');
  var pw = form ? form.querySelector('input[name="password"]') : null;
  if (pw) {
    pw.setAttribute('type', toggle.checked ? 'text' : 'password');
  }
});

document.addEventListener('click', function (ev) {
  var el = ev.target.closest('[data-mozilla-ui-reset]');
  if (!el) {
    return;
  }
  ev.preventDefault();
  // Send event to GA for metrics/reporting purposes.
  trackEvent('refresh_firefox_click');
  UITour.resetFirefox();
});

document.addEventListener('click', function (ev) {
  var el = ev.target.closest('[data-mozilla-ui-preferences]');
  if (!el) {
    return;
  }
  ev.preventDefault();
  UITour.openPreferences(el.dataset.mozillaUiPreferences);
});

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', ready);
} else {
  ready();
}
