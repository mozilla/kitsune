/*jshint*/
/*global gettext, Modernizr*/
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
        if ($this.data('close-memory') == 'remember') {
          if (Modernizr.localstorage) {
            localStorage.setItem($this.data('close-id') + '.closed', true);
          }
        }
      } else {
        $this.parent().hide();
      }
    });

    $('[data-close-memory="remember"]').each(function() {
      var id = $(this).data('close-id');
      if (id) {
        if (localStorage.getItem(id + '.closed') === 'true') {
          $('#' + id).hide();
        }
      }
    });

    $('[data-toggle]').each(function() {
        var $this = $(this);
        var $target = ($this.data('toggle-target')) ? $($this.data('toggle-target')) : $this;
        var trigger = ($this.data('toggle-trigger')) ? $this.data('toggle-trigger') : 'click';

        $this.on(trigger, function(ev) {
            ev.preventDefault();
            $target.toggleClass($this.data('toggle'));
            return false;
        });
    });

    $('[data-ui-type="tabbed-view"]').each(function() {
      var $tv = $(this);
      var $tabs = $tv.children('[data-tab-role="tabs"]').children();
      var $panels = $tv.children('[data-tab-role="panels"]').children();

      $tabs.each(function(i) {
        $(this).on('click', function() {
          $panels.hide();
          $panels.eq(i).show();
          $tabs.removeClass('selected');
          $tabs.eq(i).addClass('selected');
        })
      });

      $tabs.first().trigger('click');
    });

    $('.btn, a').each(function() {
      var $this = $(this);
      var $form = $this.closest('form');
      var type = $this.attr('data-type');
      var trigger = $this.attr('data-trigger');

      if (type === 'submit') {
        // Clicking the element will submit a form.

        if ($this.attr('data-form')) {
          $form = $('#' + $this.attr('data-form'));
        }

        $this.on('click', function(ev) {
          var name = $this.attr('data-name');
          var value = $this.attr('data-value');

          ev.preventDefault();

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
      } else if (trigger === 'click') {
        // Trigger a click on another element.

        $this.on('click', function(ev) {
          ev.preventDefault();
          $($this.attr('data-trigger-target'))[0].click();
          return false;
        });
      }
    });

    var foldingSelectors = '.folding-section, [data-ui-type="folding-section"]';

    $('body').on('click', foldingSelectors + ' header', function() {
      $(this).closest(foldingSelectors).toggleClass('collapsed');
    });

    $('form[data-confirm]').on('submit', function() {
      return confirm($(this).data('confirm-text'));
    });
  });

  $(window).load(function() {
    $('[data-ui-type="carousel"]').each(function() {
      var $this = $(this);
      var $container = $(this).children().first()

      var width = 0;
      var height = 0;

      $container.children().each(function() {
        if (height < $(this).outerHeight()) {
          height = $(this).outerHeight();
        }
        width += $(this).outerWidth() + parseInt($(this).css('marginRight')) + parseInt($(this).css('marginLeft'));
      });

      $this.css('height', height + 'px');
      $container.css({'width': width + 'px', 'height': height + 'px'});
      $container.children().css('height', height + 'px');

      var $left = $('#' + $this.data('left'));
      var $right = $('#' + $this.data('right'));

      var scrollInterval;

      $left.on('mouseover', function() {
        scrollInterval = setInterval(function() {
          $this.scrollLeft($this.scrollLeft() - 1);
        }, 1);
      });

      $left.on('mouseout', function() {
        clearInterval(scrollInterval);
      });

      $right.on('mouseover', function() {
        scrollInterval = setInterval(function() {
          $this.scrollLeft($this.scrollLeft() + 1);
        }, 1);
      });

      $right.on('mouseout', function() {
        clearInterval(scrollInterval);
      });
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
