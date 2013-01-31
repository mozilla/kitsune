(function($) {
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
            $('#' + $(this).data('submit')).submit();
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

        // iOS overscroll fix
        document.addEventListener('touchmove', function(e) {
            e.preventDefault();
        }, false);

        $('.scrollable').each(function() {
            var y = 0;
            var isTop = false;
            var isBottom = false;

            this.addEventListener('touchstart', function(e) {
                y = e.pageY;
                isTop = this.scrollTop <= 0;
                isBottom = this.scrollHeight - this.scrollTop <= this.clientHeight;
            }, true);

            this.addEventListener('touchmove', function(e) {
                var scrollUp = e.pageY > y;

                if ((scrollUp && !isTop) || (!scrollUp && !isBottom)) {
                    e.stopPropagation();
                } else {
                    e.preventDefault();
                }
            }, true);
        });
    });
})(jQuery)
