k = {};

(function($) {
    var UNSAFE_CHARS = {
      '&': '&amp;',
      '<': '&lt;',
      '>': '&gt;',
      "'": '&#39;',
      '"': '&quot;'
    };

    k.safeString = function(str) {
      if (str) {
        return str.replace(new RegExp('[&<>\'"]', 'g'),
            function(m) { return UNSAFE_CHARS[m]; });
      }
      return str;
    };

    k.safeInterpolate = function(fmt, obj, named) {
      if (named) {
        for (var j in obj) {
          obj[j] = k.safeString(obj[j]);
        }
      } else {
        for (var i=0, l=obj.length; i<l; i++) {
          obj[i] = k.safeString(obj[i]);
        }
      }
      return interpolate(fmt, obj, named);
    };

    $(function() {
        // Menu toggling
        $('#menu-button').on('click', function() {
            $('#page').toggleClass('exposed');
        });

        function showNotification(notification) {
            $(notification).first().fadeIn(600, function() {
                $(this).delay(5000).fadeOut(600, function() {
                    var next = $(this).next();
                    $(this).remove();
                    showNotification(next);
                });
            });
        }

        $('#cancel-button').on('click', function() {
           if (!confirm(gettext('Are you sure you wish to cancel?'))) {
               return false;
           }
        });

        showNotification($('#notifications > li').fadeOut(0));

        $(document).on('click', '.overlay > header', function() {
            $(this).closest('.overlay').hide();
        });

        $(document).on('click', '.pulldown-menu .pulldown-handle', function() {
            $(this).closest('.pulldown-menu').toggleClass('open');
        });

        $(document).on('click', '[data-overlay]', function() {
            var overlay = $(this).data('overlay');
            if (overlay) {
                $('#' + overlay).show();
            }
        });

        $(document).on('click', '[data-show]', function() {
            $('#' + $(this).data('show')).css('display', '');
        });

        $(document).on('click', '[data-hide]', function() {
            $('#' + $(this).data('hide')).hide();
        });

        $(document).on('click', '[data-expand]', function() {
            $('#' + $(this).data('expand')).addClass('expanded');
        });

        $(document).on('click', '[data-submit]', function() {
            var $form = $('#' + $(this).data('submit'));
            var name = $(this).data('name');
            if (name) {
              if (!$form.has('input[name="' + name + '"]').length) {
                $form.append('<input name="' + name + '" value="1" type="hidden">');
              }
            }
            $form.submit();
        });

        $(document).on('click', '[data-toggle-class]', function() {
            $('body').toggleClass($(this).data('toggle-class'));
        });

        $(document).on('click', '.collapsable .toggle', function() {
            $(this).closest('.collapsable').toggleClass('expanded');
        });

        // Swipeable lists
        $('.swipeable').each(function() {
            var width = 0;
            $(this).children('ul').find('li').each(function() {
                width += $(this).outerWidth() + parseInt($(this).css('marginLeft')) + parseInt($(this).css('marginRight'));
            });
            $(this).children('ul').css('width', width + 'px');
        });

        // iOS Standalone Web App Fix
        if (("standalone" in window.navigator) && window.navigator.standalone) {
            $(document).on('click', 'a', function(event) {
                var href = $(event.target).attr('href');

                if (href) {
                    event.preventDefault();
                    location.href = href;
                }
            });
        }

        if ($('body').is('.aaq')) {
            // Pre-populate form with user's system info
            new AAQSystemInfo($('#question-form'));
        }
    });
})(jQuery)
