/* global gettext:false, Modernizr:false, _:false, jQuery:false, Mailcheck:false,
          interpolate:false, Mozilla:false, trackEvent:false */
(function($) {
  'use strict';

  $(document).ready(function() {
    initFolding();
    initAnnouncements();

    $('#delete-profile-username-input').keyup(function(ev) {
      var username = $('#delete-profile-username').val();
      var inputUsername = $('#delete-profile-username-input').val();
      if (inputUsername === username) {
        $('#delete-profile-button').prop('disabled', false);
      } else {
        $('#delete-profile-button').prop('disabled', true);
      }
    });

    $(window).scroll(_.throttle(function() {
      if ($(window).scrollTop() > $('body > header').outerHeight()) {
        $('body').addClass('scroll-header');
      } else {
        $('body').removeClass('scroll-header');
      }
    }, 100));

    if ($.datepicker) {
      $('input[type="date"]').datepicker();
    }

    $('.ui-truncatable .show-more-link').click(function(ev) {
      ev.preventDefault();
      $(this).closest('.ui-truncatable').removeClass('truncated');
    });

    $(document).on('click', '.close-button', function() {
      var $this = $(this);
      var $target;
      if ($this.data('close-id')) {
        $target = $('#' + $this.data('close-id'));
        if ($this.data('close-memory') === 'remember') {
          if (Modernizr.localstorage) {
            localStorage.setItem($this.data('close-id') + '.closed', true);
          }
        }
      } else {
        $target = $this.parent();
      }
      if ($this.data('close-type') === 'remove') {
        $target.remove();
      } else {
        $target.hide();
      }
    });

    $(document).on('change', 'select[data-submit]', function() {
      var $this = $(this);
      var $form = ($this.data('submit')) ? $('#' + $this.data('submit')) : $this.closest('form');
      $form.submit();
    });

    $('[data-close-memory="remember"]').each(function() {
      var $this = $(this);
      var id = $this.data('close-id');
      if (id) {
        if (Modernizr.localstorage) {
          if (localStorage.getItem(id + '.closed') === 'true') {
            var $target = $('#' + id);
            if ($this.data('close-type') === 'remove') {
              $target.remove();
            } else {
              $('#' + id).hide();
            }
          }
        }
      }
    });

    $('[data-toggle]').each(function() {
      var $this = $(this);
      var $target = ($this.data('toggle-target')) ? $($this.data('toggle-target')) : $this;
      var trigger = ($this.data('toggle-trigger')) ? $this.data('toggle-trigger') : 'click';
      var targetId = $target.attr('id');

      if ($this.data('toggle-sticky') && targetId) {
        if (Modernizr.localstorage) {
          var targetClasses = localStorage.getItem(targetId + '.classes') || '[]';
          targetClasses = JSON.parse(targetClasses);
          $target.addClass(targetClasses.join(' '));
        }
      }

      $this.on(trigger, function(ev) {
        ev.preventDefault();
        var classname = $this.data('toggle');
        $target.toggleClass(classname);

        if ($this.data('toggle-sticky') && targetId) {
          if (Modernizr.localstorage) {
            var classes = localStorage.getItem(targetId + '.classes') || '[]';
            classes = JSON.parse(classes);
            var i = classes.indexOf(classname);

            if ($target.hasClass(classname) && i === -1) {
              classes.push(classname);
            } else if (!$target.hasClass(classname) && i > -1) {
              classes.splice(i, 1);
            }

            localStorage.setItem(targetId + '.classes', JSON.stringify(classes));
          }
        }
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
        });
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
      return confirm($(this).data('confirm-text')); // eslint-disable-line
    });
  });

  $(window).load(function() {
    correctFixedHeader();
    $('[data-ui-type="carousel"]').each(function() {
      var $this = $(this);
      var $container = $(this).children().first();

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

  function correctFixedHeader() {
    var headerHeight = document.querySelector('header');
    var scrollHeight = headerHeight.scrollHeight;
    if (window.location.hash && document.querySelector(window.location.hash)) {
      window.scrollBy(0, -scrollHeight);
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

  $(document).on('click', '#show-password', function() {
    var $form = $(this).closest('form');
    var $pw = $form.find('input[name="password"]');
    $pw.attr('type', (this.checked) ? 'text' : 'password');
  });

  var validate_field_cb = function() {
    var $this = $(this);
    var $v = $this.closest('[data-validate-url]');
    var url = $v.data('validate-url');
    var $label = $v.find('.validation-label');

    var extras = $v.data('validate-extras');

    if (_.contains(extras, 'email')) {
      var domain = $this.val().split('@').pop();
      var corrected = Mailcheck.findClosestDomain(domain, ['gmail.com', 'yahoo.com', 'hotmail.com']);

      var ignoreList = $this.data('mailcheck-ignore') || [];

      if (corrected && corrected !== domain && !_.contains(ignoreList, $this.val())) {
        var $ignore = $('<a />').attr('href', '#').addClass('ignore-email').text(gettext('No, ignore'));
        $ignore.on('click', function(ev) {
          ev.preventDefault();
          ignoreList.push($this.val());
          $this.data('mailcheck-ignore', ignoreList);
          $this.trigger('change');
        });

        $label.removeClass('valid');
        $label.text(interpolate(gettext('Did you mean %s?'), [corrected]));
        $label.append($ignore);
        $label.show();

        return false;
      } else {
        $label.hide();
      }
    }

    $.getJSON(url, {
      field: $this.attr('name'),
      value: $this.val()
    }, function(data) {
      if ($this.val().length) {
        if (data.valid) {
          $label.addClass('valid');
          $label.text($v.data('valid-label'));
        } else {
          $label.removeClass('valid');
          $label.text(data.error);
        }
        $label.show();
      } else {
        $label.hide();
      }
    });
  };

  $(document).on('keyup', '[data-validate-url] input', _.throttle(validate_field_cb, 200));
  $(document).on('change', '[data-validate-url] input', _.throttle(validate_field_cb, 200));
  $(window).on('hashchange', correctFixedHeader);

  $(document).on('click', '[data-mozilla-ui-reset]', function(ev) {
    ev.preventDefault();
    if (Mozilla && Mozilla.UITour) {
      // Send event to GA for metrics/reporting purposes.
      trackEvent('Refresh Firefox', 'click refresh button');

      if (JSON.parse($('body').data('waffle-refresh-survey'))) {
        $.cookie('showFirefoxResetSurvey', '1', {expires: 365});
      }

      Mozilla.UITour.resetFirefox();
    }
    return false;
  });

})(jQuery);
