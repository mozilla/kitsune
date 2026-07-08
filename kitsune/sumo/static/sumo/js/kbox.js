/**
 * A KBox type and a corresponding (transitional) jQuery plugin.
 *
 * So, what is a kbox?
 * A kbox can be a modal dialog or a (dhtml, not window) popup or a ...
 * The kbox can be configured programatically or using data-* attributes.
 * Default styles are in kbox.css.
 *
 * Usage
 *      Declarative:
 *      <a id="example-id" ...>Click here to show modal</a>
 *      <div class="kbox" title="A modal dialog" data-target="#example-id" data-modal="true">
 *          .... modal content ....
 *      </div>
 *
 *      Programatic:
 *      var kbox = new KBox('<p>Some content</p>', {
 *          title: 'KBox Title'
 *      });
 *      kbox.open();
 *
 *      Mixed:
 *      [HTML]
 *      <a id="a-id" ...>Click ...</a>
 *      <div id="kbox-id" class="kbox" data-target="#a-id">...content...</div>
 *      [JavaScript]
 *      var kbox = document.getElementById('kbox-id').kbox; // Gets the kbox instance.
 *      kbox.updateOptions({
 *          preOpen: function() {
 *              // If isFormValid() returns false, the kbox doesn't open;
 *              return isFormValid();
 *          }
 *      });
 *
 * Options
 *      clickTarget / data-target:
 *          DOM elements or CSS Selector to target(s)
 *          that will trigger the kbox to open on click. Optional.
 *      closeOnEsc / data-close-on-esc:
 *          Close the kbox on ESC. Default: true.
 *      closeOnOutClick: / data-close-on-out-click:
 *          Close the kbox on any click outside of it. Default: false.
 *      container / data-container:
 *          DOM element for appending the kbox. Optional.
 *          If html string is passed as the content of the kbox, container
 *          will default to document.body.
 *      destroy / data-destroy:
 *          Clean up DOM changes on close. Default: false.
 *      id / data-id:
 *          An id for the kbox container. Optional.
 *      modal / data-modal:
 *          Do we need to make the kbox modal? Adds a background overlay.
 *          Default: false.
 *      position / data-position:
 *          Where to position the kbox.
 *              'center': (default) centers the kbox in the window
 *              'none': doesn't do any positioning so you can do it in CSS
 *              (TODO:) 'force-center': keeps kbox center as window scrolls
 *      preOpen:
 *          A function to call before opening the kbox. If the function
 *          returns false, the kbox isn't opened. Optional.
 *      preClose:
 *          A function to call before closing the kbox. If the function
 *          returns false, the kbox isn't closed. Optional.
 *      template:
 *          Override the template to use for creating the modal.
 *      title:
 *          The kbox's title.
 *      windowMargin:
 *          Minimum margin between the kbox and the edge of the window.
 */

import { toElement, toElements } from "sumo/js/utils/dom";

var TEMPLATE = (
  '<div class="kbox-container">' +
  '<div class="kbox-header">' +
  '<div class="kbox-title"></div>' +
  '<a href="#close" class="kbox-close">&#x2716;</a>' +
  '</div>' +
  '<div class="kbox-wrap"><div class="kbox-placeholder"/></div>' +
  '</div>'
),
  OVERLAY = '<div id="kbox-overlay"></div>';

// Parse an HTML string into its first element.
function parseHTML(html) {
  var template = document.createElement('template');
  template.innerHTML = typeof html === 'string' ? html.trim() : '';
  return template.content.firstElementChild;
}

// Read a data-* attribute with the same value coercion jQuery's .data() did
// (true/false/null/numbers/JSON get parsed; everything else stays a string).
function dataAttr(el, key) {
  var camel = key.replace(/-([a-z])/g, function (_, c) {
    return c.toUpperCase();
  });
  var raw = el.dataset[camel];
  if (raw === undefined) {
    return undefined;
  }
  if (raw === 'true') return true;
  if (raw === 'false') return false;
  if (raw === 'null') return null;
  if (raw === +raw + '') return +raw;
  if (/^(?:\{[\s\S]*\}|\[[\s\S]*\])$/.test(raw)) {
    try {
      return JSON.parse(raw);
    } catch (e) {
      return raw;
    }
  }
  return raw;
}

// The KBox type
export default function KBox(el, options) {
  KBox.prototype.init.call(this, el, options);
}

KBox.prototype = {
  init: function (el, options) {
    var self = this;
    self.el = el;
    self.html = typeof el === 'string' ? el : false;
    self.element = self.html ? parseHTML(self.html) : toElement(el);
    options = Object.assign({
      // defaults
      clickTarget: dataAttr(self.element, 'target'),
      closeOnEsc: dataAttr(self.element, 'close-on-esc') === undefined ?
        true : !!dataAttr(self.element, 'close-on-esc'),
      closeOnOutClick: !!dataAttr(self.element, 'close-on-out-click'),
      container: self.html && document.body,
      destroy: !!dataAttr(self.element, 'destroy'),
      id: dataAttr(self.element, 'id'),
      modal: !!dataAttr(self.element, 'modal'),
      position: dataAttr(self.element, 'position') || 'center',
      preOpen: false,
      preClose: false,
      template: TEMPLATE,
      title: self.element.getAttribute('title') ||
        self.element.getAttribute('data-title'),
      windowMargin: parseInt(dataAttr(self.element, 'viewport-margin') ?? 20, 10),
    }, options);
    self.options = options;
    self.clickTargets = options.clickTarget ? toElements(options.clickTarget) : [];
    self.container = options.container ? toElement(options.container) : null;
    self.rendered = false; // did we render out yet?
    self.placeholder = null; // placeholder used if we need to move self.element in the DOM.
    self.kbox = null;
    self.isOpen = false;

    // Make the instance accessible from the DOM element.
    self.element.kbox = self;
    // Transitional bridge: not-yet-migrated consumers (dashboards.js, wiki.js)
    // still retrieve the instance via jQuery's $(el).data('kbox'). Remove once
    // those callers use element.kbox directly.
    $(self.element).data('kbox', self);

    // If we have a click target, open the kbox when it is clicked.
    self.clickTargets.forEach(function (target) {
      target.addEventListener('click', function (ev) {
        ev.preventDefault();
        self.open();
      });
    });
  },
  updateOptions: function (options) {
    // Ability to update options programmatically after kbox creation.
    var self = this;
    self.options = Object.assign(self.options, options);
    if (options.clickTarget) {
      self.clickTargets = toElements(options.clickTarget);
    }
    if (options.container) {
      self.container = toElement(options.container);
    }
  },
  render: function () {
    var self = this;
    self.kbox = parseHTML(self.options.template);

    if (self.container) {
      // The kbox will be appended to the container.
      if (self.element.parentNode) {
        // If we are attached to the DOM, save our place there
        // for putting everything back in place later.
        self.placeholder = document.createElement('div');
        self.placeholder.style.display = 'none';
        self.element.parentNode.insertBefore(self.placeholder, self.element);
      }
      self.container.appendChild(self.kbox);
    } else {
      // The kbox will go right where the element is.
      self.element.parentNode.insertBefore(self.kbox, self.element);
    }

    // Set the id if it was specified
    if (self.options.id) {
      self.kbox.setAttribute('id', self.options.id);
    }

    // Set the title if it was specified.
    if (self.options.title) {
      self.kbox.querySelector('.kbox-title').textContent = self.options.title;
    }

    // Insert the content (moves self.element into the kbox).
    self.kbox.querySelector('.kbox-placeholder').replaceWith(self.element);

    // Handle close events
    self.kbox.addEventListener('click', function (ev) {
      if (ev.target.closest('.kbox-close, .kbox-cancel')) {
        ev.preventDefault();
        self.close();
      }
    });

    self.rendered = true;
  },
  open: function () {
    var self = this;
    if (self.options.preOpen && !self.options.preOpen.call(self)) {
      // If we have a preOpen callback and it returns false,
      // we don't open anything.
      return;
    }
    if (self.isOpen) {
      return;
    }
    self.isOpen = true;
    if (!self.rendered) {
      self.render();
    }
    self.kbox.classList.add('kbox-open');
    self.handleOverflow();
    self.setPosition();
    self.addResizeHandler();
    if (self.options.modal) {
      self.createOverlay();
    }

    // Handle ESC
    if (self.options.closeOnEsc) {
      self.keypressHandler = function (ev) {
        if (ev.key === 'Escape' || ev.keyCode === 27) {
          self.close();
        }
      };
      document.addEventListener('keydown', self.keypressHandler);
    }

    // Handle outside clicks
    if (self.options.closeOnOutClick) {
      self.clickHandler = function (ev) {
        if (!ev.target.closest('.kbox-container')) {
          // The click isn't inside the kbox, so lets close it.
          self.close();
        }
      };
      setTimeout(function () { // so it doesn't get triggered on this click
        document.body.addEventListener('click', self.clickHandler);
      }, 0);
    }
  },
  addResizeHandler: function () {
    var self = this;
    // If position is none, return early instead of adding a listener that will never do anything
    if (self.options.position === 'none') {
      return;
    }
    self.resizeHandler = function () {
      if (self.resizeFrame) {
        return;
      }
      self.resizeFrame = window.requestAnimationFrame(function () {
        self.resizeFrame = null;
        self.setPosition();
      });
    };
    window.addEventListener('resize', self.resizeHandler);
  },
  removeResizeHandler: function () {
    var self = this;
    if (self.resizeHandler) {
      window.removeEventListener('resize', self.resizeHandler);
      if (self.resizeFrame) {
        window.cancelAnimationFrame(self.resizeFrame);
      }
      delete self.resizeFrame;
      delete self.resizeHandler;
    }
  },
  setPosition: function (position) {
    var self = this;
    const minMargin = self.options.windowMargin;
    if (!position) {
      position = self.options.position;
    }
    if (position === 'none' || !self.kbox) {
      return;
    }
    if (position === 'center') {
      let windowWidth = window.innerWidth;
      let windowHeight = window.innerHeight;

      // Reset height and width limitations to get the actual initial kbox size
      self.resetOverflow();

      let modalWidth = self.kbox.offsetWidth;
      let modalHeight = self.kbox.offsetHeight;

      let left = Math.max((windowWidth - modalWidth) / 2, minMargin);
      let top = Math.max((windowHeight - modalHeight) / 2, minMargin);

      self.kbox.style.left = left + 'px';
      self.kbox.style.top = top + 'px';
      self.kbox.style.right = 'inherit';
      self.kbox.style.bottom = 'inherit';
      self.kbox.style.position = 'fixed';

      self.handleOverflow();
    }
  },
  handleOverflow: function () {
    var self = this;
    const minMargin = self.options.windowMargin;

    let windowWidth = window.innerWidth;
    let windowHeight = window.innerHeight;
    let rect = self.kbox.getBoundingClientRect();

    if (rect.right > windowWidth - minMargin) {
      self.kbox.style.maxWidth =
        Math.max(windowWidth - minMargin - rect.left, minMargin) + 'px';
    }
    else if (rect.right < windowWidth - minMargin) {
      self.kbox.style.maxWidth = '';
    }

    // Due to max-width, kbox height may have changed.
    rect = self.kbox.getBoundingClientRect();

    if (rect.bottom > windowHeight) {
      self.kbox.style.maxHeight =
        Math.max(windowHeight - minMargin - rect.top, minMargin) + 'px';
      self.kbox.style.overflowY = 'auto';
    }
    else if (rect.bottom < windowHeight - minMargin) {
      self.kbox.style.maxHeight = '';
      self.kbox.style.overflowY = '';
    }
  },
  resetOverflow: function () {
    var self = this;
    self.kbox.style.maxWidth = '';
    self.kbox.style.maxHeight = '';
    self.kbox.style.overflowY = '';
  },
  close: function () {
    var self = this;
    if (self.options.preClose && !self.options.preClose.call(self)) {
      // If we have a preClose callback and it returns false,
      // we don't open anything.
      return;
    }
    if (!self.isOpen) {
      return;
    }
    self.isOpen = false;
    self.kbox.classList.remove('kbox-open');
    self.removeResizeHandler();
    if (self.options.modal) {
      self.destroyOverlay();
    }
    if (self.options.destroy) {
      self.destroy();
    }
    if (self.options.closeOnEsc) {
      document.removeEventListener('keydown', self.keypressHandler);
    }
    if (self.options.closeOnOutClick) {
      document.body.removeEventListener('click', self.clickHandler);
    }
  },
  destroy: function () {
    // return DOM to how it was originally, if possible.
    var self = this;
    self.removeResizeHandler();
    if (self.container && self.placeholder) {
      self.placeholder.replaceWith(self.element);
    }
    self.kbox.remove();
  },
  createOverlay: function () {
    var self = this;
    self.overlay = parseHTML(OVERLAY);
    self.kbox.parentNode.insertBefore(self.overlay, self.kbox);
  },
  destroyOverlay: function () {
    if (this.overlay) {
      this.overlay.remove();
      delete this.overlay;
    }
  }
};

// Transitional jQuery plugin: not-yet-migrated consumers (gallery.js, wiki.js)
// still call $('.kbox').kbox(). Remove once those callers use `new KBox(...)`.
$.fn.kbox = function (options) {
  return this.each(function () {
    new KBox(this, options);
  });
};

// Initialize declared kboxes.
document.querySelectorAll('.kbox').forEach(function (el) {
  new KBox(el);
});
