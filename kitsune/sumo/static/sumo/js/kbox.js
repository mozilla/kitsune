/**
 * A KBox type and a corresponding jQuery plugin.
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
 *      var kbox = $('kbox-id').data('kbox'); // Gets the kbox instance.
 *      kbox.updateOptions({
 *          preOpen: function() {
 *              // If isFormValid() returns false, the kbox doesn't open;
 *              return isFormValid();
 *          }
 *      });
 *
 * Options
 *      clickTarget / data-target:
 *          jQuery or DOM elements or CSS Selector to target(s)
 *          that will trigger the kbox to open on click. Optional.
 *      closeOnEsc / data-close-on-esc:
 *          Close the kbox on ESC. Default: true.
 *      closeOnOutClick: / data-close-on-out-click:
 *          Close the kbox on any click outside of it. Default: false.
 *      container / data-container:
 *          jQuery or DOM element for appending the kbox. Optional.
 *          If html string is passed as the content of the kbox, container
 *          will default to $('body').
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

// The KBox type
export default function KBox(el, options) {
  KBox.prototype.init.call(this, el, options);
}

KBox.prototype = {
  init: function (el, options) {
    var self = this;
    self.el = el;
    self.html = typeof el === 'string' && el;
    self.$el = $(el);
    options = $.extend({
      // defaults
      clickTarget: self.$el.data('target'),
      closeOnEsc: self.$el.data('close-on-esc') === undefined ?
        true : !!self.$el.data('close-on-esc'),
      closeOnOutClick: !!self.$el.data('close-on-out-click'),
      container: self.html && $('body'),
      // TODO: maxHeight: self.$el.data('max-height') || 'window',
      destroy: !!self.$el.data('destroy'),
      id: self.$el.data('id'),
      modal: !!self.$el.data('modal'),
      position: self.$el.data('position') || 'center',
      preOpen: false,
      preClose: false,
      template: TEMPLATE,
      title: self.$el.attr('title') || self.$el.attr('data-title'),
      windowMargin: parseInt(self.$el.data('viewport-margin') ?? 20, 10),
    }, options);
    self.options = options;
    self.$clickTarget = options.clickTarget && $(options.clickTarget);
    self.$container = options.container && $(options.container);
    self.rendered = false; // did we render out yet?
    self.$ph = false; // placeholder used if we need to move self.$el in the DOM.
    self.$kbox = $();
    self.isOpen = false;

    // Make the instance accessible from the DOM element.
    self.$el.data('kbox', self);

    // If we have a click target, open the kbox when it is clicked.
    if (self.$clickTarget) {
      self.$clickTarget.on("click", function (ev) {
        ev.preventDefault();
        self.open();
      });
    }

  },
  updateOptions: function (options) {
    // Ability to update options programmatically after kbox creation.
    var self = this;
    self.options = $.extend(self.options, options);
    self.$clickTarget = options.clickTarget && $(options.clickTarget);
    self.$container = options.container && $(options.container);
  },
  render: function () {
    var self = this;
    self.$kbox = $(self.options.template);

    if (self.$container) {
      // The kbox will be appended to the container.
      if (self.$el.parent().length) {
        // If we are attached to the DOM, save our place there
        // for putting everything back in place later.
        self.$ph = self.$el.before('<div style="display:none;"/>').prev();
      }
      self.$kbox.appendTo(self.$container);
    } else {
      // The kbox will go right where $el is.
      self.$el.before(self.$kbox);
    }

    // Set the id if it was specified
    if (self.options.id) {
      self.$kbox.attr('id', self.options.id);
    }

    // Set the title if it was specified.
    if (self.options.title) {
      self.$kbox.find('.kbox-title').text(self.options.title);
    }

    // Insert the content.
    self.$kbox.find('.kbox-placeholder').replaceWith(self.$el.detach());

    // Handle close events
    self.$kbox.on('click', '.kbox-close, .kbox-cancel', function (ev) {
      ev.preventDefault();
      self.close();
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
    self.$kbox.addClass('kbox-open');
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
      $(document).on('keydown', self.keypressHandler);
    }

    // Handle outside clicks
    if (self.options.closeOnOutClick) {
      self.clickHandler = function (ev) {
        if ($(ev.target).closest('.kbox-container').length === 0) {
          // The click isn't inside the kbox, so lets close it.
          self.close();
        }
      };
      setTimeout(function () { // so it doesn't get triggered on this click
        $('body').on("click", self.clickHandler);
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
    $(window).on('resize', self.resizeHandler);
  },
  removeResizeHandler: function () {
    var self = this;
    if (self.resizeHandler) {
      $(window).off('resize', self.resizeHandler);
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
    if (position === 'none' || !self.$kbox.length) {
      return;
    }
    if (position === 'center') {
      let windowWidth = $(window).width();
      let windowHeight = $(window).height();

      // Reset height and width limitations to get the actual initial kbox size
      self.resetOverflow();

      let modalWidth = self.$kbox.outerWidth();
      let modalHeight = self.$kbox.outerHeight();

      let left = Math.max((windowWidth - modalWidth) / 2, minMargin);
      let top = Math.max((windowHeight - modalHeight) / 2, minMargin);

      self.$kbox.css({
        'left': left,
        'top': top,
        'right': 'inherit',
        'bottom': 'inherit',
        'position': 'fixed'
      });

      self.handleOverflow();
    }
  },
  handleOverflow: function () {
    var self = this;
    const minMargin = self.options.windowMargin;

    let windowWidth = $(window).width();
    let windowHeight = $(window).height();
    let rect = self.$kbox[0].getBoundingClientRect();

    if (rect.right > windowWidth - minMargin) {
      self.$kbox.css({
        'max-width': Math.max(windowWidth - minMargin - rect.left, minMargin)
      });
    }
    else if (rect.right < windowWidth - minMargin) {
      self.$kbox.css({
        'max-width': ''
      });
    }

    // Due to max-width, kbox height may have changed.
    rect = self.$kbox[0].getBoundingClientRect();

    if (rect.bottom > windowHeight) {
      self.$kbox.css({
        'max-height': Math.max(windowHeight - minMargin - rect.top, minMargin),
        'overflow-y': 'auto'
      });
    }
    else if (rect.bottom < windowHeight - minMargin) {
      self.$kbox.css({
        'max-height': '',
        'overflow-y': ''
      });
    }
  },
  resetOverflow: function () {
    var self = this;
    self.$kbox.css({
      'max-width': '',
      'max-height': '',
      'overflow-y': ''
    });
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
    self.$kbox.removeClass('kbox-open');
    self.removeResizeHandler();
    if (self.options.modal) {
      self.destroyOverlay();
    }
    if (self.options.destroy) {
      self.destroy();
    }
    if (self.options.closeOnEsc) {
      $('body').off('keydown', self.keypressHandler);
    }
    if (self.options.closeOnOutClick) {
      $('body').off('click', self.clickHandler);
    }
  },
  destroy: function () {
    // return DOM to how it was originally, if possible.
    var self = this;
    self.removeResizeHandler();
    if (self.$container && self.$ph) {
      self.$ph.replaceWith(self.$el.detach());
    }
    self.$kbox.remove();
  },
  createOverlay: function () {
    var self = this;
    self.$overlay = $(OVERLAY);
    self.$kbox.before(self.$overlay);
  },
  destroyOverlay: function () {
    if (this.$overlay) {
      this.$overlay.remove();
      delete this.$overlay;
    }
  }
};

// Create the jQuery plugin.
$.fn.kbox = function (options) {
  return this.each(function () {
    new KBox(this, options);
  });
};

// Initialize declared kboxes.
$('.kbox').kbox();
