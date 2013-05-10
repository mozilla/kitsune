/*jshint*/
/*global Modernizr*/
;(function($) {
  "use strict";

  $(document).ready(function() {
    initFolding();

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

      if ($this.attr('data-type') === 'submit') {
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

  function notifyOutdatedFirefox() {
    var b = BrowserDetect.browser;
    var v = BrowserDetect.version;

    if (Modernizr.localstorage) {
      var closed = localStorage.getItem('notify-outdated.closed') === 'true';
    }

    if (b == 'fx' && (v <= 3.6 || (v >= 12 && v <= 16)) && !closed) {
      // Ensure that the notify bar appears above tabzilla's panel
      $(document).on('click', '#tabzilla', function() {
        $('body').prepend($('#notify-outdated-bar'));
      });

      var $notifyBar = $('<div />').attr('id', 'notify-outdated-bar');

      var $container = $('<div />').addClass('grid_12');
      $notifyBar.append($container);
      $container.wrap($('<div />').addClass('container_12'));

      var $closeButton = $('<div />').addClass('close-button');
      $closeButton.data('close-id', 'notify-outdated-bar');
      $container.append($closeButton);

      var $downloadButton = $('<a />').addClass('download-button');
      $downloadButton.attr('href', 'http://www.mozilla.org/firefox#desktop');
      $downloadButton.html(gettext('Upgrade Firefox'));
      $container.prepend($downloadButton);

      $container.prepend($('<span />').html(gettext('Your Firefox is out of date and may contain a security risk!')));

      if (Modernizr.localstorage) {
        $closeButton.on('click', function() {
          localStorage.setItem('notify-outdated.closed', true);
        });
      }

      $('body').prepend($notifyBar);
    }
  }

})(jQuery);
