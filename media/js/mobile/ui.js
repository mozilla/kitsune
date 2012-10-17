(function($) {
    $(function() {
        // Menu toggling
        $('#menu-button').on('click', function() {
            var $page = $('#page');
            var $nav = $('body > nav');

            var animation = {};

            if ($('body').data('orientation') === 'right') {
                if ($page.css('right') === '0px') {
                    animation.right = $nav.outerWidth();
                } else {
                    animation.right = 0;
                }
            } else {
                if ($page.css('left') === '0px') {
                    animation.left = $nav.outerWidth();
                } else {
                    animation.left = 0;
                }
            }

            $page.animate(animation);
        });

        $('.overlay > header').on('click', function() {
            $(this).closest('.overlay').hide();
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
    });
})(jQuery)