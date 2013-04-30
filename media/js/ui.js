/*jshint*/
/*global Modernizr*/
;(function($) {
  "use strict";

  $(document).ready(function() {
    initFolding();

    $('.ui-truncatable .show-more-link').click(function(ev) {
      ev.preventDefault();
      $(this).closest('.ui-truncatable').removeClass('truncated');
    });

    $('.close-button').click(function() {
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

})(jQuery);
