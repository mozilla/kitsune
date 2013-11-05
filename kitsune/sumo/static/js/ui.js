/*jshint*/
/*global Modernizr*/
;(function($) {
  "use strict";

  $(document).ready(function() {
    initFolding();
    initAnnouncements();

    // Non supported Firefox version
    notifyOutdatedFirefox();

    $('.ui-truncatable .show-more-link').click(function(ev) {
      ev.preventDefault();
      $(this).closest('.ui-truncatable').removeClass('truncated');
    });

    $(document).on('click', '.close-button', function() {
      var $this = $(this);
      if ($this.data('close-id')) {
        $('#' + $this.data('close-id')).hide();
      } else {
        $this.parent().hide();
      }
    });

    $('.btn, a').each(function() {
      var $this = $(this);
      var $form = $this.closest('form');
      var type = $this.attr('data-type');

      if (type === 'submit') {
        // Clicking the element will submit a form.

        if ($this.attr('data-form')) {
          $form = $('#' + $this.attr('data-form'));
        }

        $this.on('click', function() {
          var name = $this.attr('data-name');
          var value = $this.attr('data-value');

          if (name) {
            var $input = $('<input type="hidden">');

            $input.attr('name', name);

            if (value) {
              $input.val(value);
            } else {
              $input.val('1');
            }

            $form.append($input);
          }

          if ($this.attr('data-nosubmit') !== '1') {
            $form.trigger('submit');
          }
        });
      } else if (type === 'click') {
        // Clicking the element will click somewhere else.

        $this.on('click', function(ev) {
          ev.preventDefault();
          $($this.attr('data-click-selector')).click();
          return false;
        });
      }
    });

    var foldingSelectors = '.folding-section, [data-ui-type="folding-section"]';

    $('body').on('click', foldingSelectors + ' header', function() {
      $(this).closest(foldingSelectors).toggleClass('collapsed');
    });
  });

  function initFolding() {
    var $folders = $('.sidebar-folding > li');
    // When a header is clicked, expand/contract the menu items.
    $folders.children('a, span').click(function() {
      var $parent = $(this).parent();
      $parent.toggleClass('selected');
      // If local storage is available, store this for future page loads.
      if (Modernizr.localstorage) {
        var id = $parent.attr('id');
        var folded = $parent.hasClass('selected');
        if (id) {
          localStorage.setItem(id + '.folded', folded);
        }
      }
      // prevent default
      return false;
    });

    // If local storage is available, load the folded/unfolded state of the
    // menus from local storage and apply it.
    if (Modernizr.localstorage) {
      $folders.each(function() {
        var $this = $(this);
        var id = $this.attr('id');

        if (id) {
          var folded = localStorage.getItem(id + '.folded');

          if (folded === 'true') {
            $this.addClass('selected');
          } else if (folded === 'false') {
            $this.removeClass('selected');
          }
        }
      });
    }
  }

  function initAnnouncements() {
    var $announcements = $('#announcements');

    $(document).on('click', '#tabzilla', function() {
      $('body').prepend($announcements);
    });

    if (Modernizr.localstorage) {
      // When an announcement is closed, remember it.
      $announcements.on('click', '.close-button', function() {
        var id = $(this).closest('.announce-bar').attr('id');
        localStorage.setItem(id + '.closed', true);
      });

      // If an announcement has not been hidden before, show it.
      $announcements.find('.announce-bar').each(function() {
        var $this = $(this);
        var id = $this.attr('id');
        if (localStorage.getItem(id + '.closed') !== 'true') {
          $this.show();
        }
      });
    } else {
      $announcements.find('.announce-bar').show();
    }
  }

  function notifyOutdatedFirefox() {
    var b = BrowserDetect.browser;
    var v = BrowserDetect.version;
    var closed = false;
    var show;

    if (Modernizr.localstorage) {
      closed = localStorage.getItem('announcement-outdated.closed') === 'true';
    }

    show = (b == 'fx') && (v <= 16 || (v >= 18 && v <= 23)) && (!closed);
    if (show) {
      $('#announce-outdated').show();
    } else {
      $('#announce-outdated').hide();
    }
  }

})(jQuery);
