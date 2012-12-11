(function($) {
    $(function() {
        // Menu toggling
        $('#menu-button').on('click', function() {
            $('#page').toggleClass('exposed');
        });

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

        $(document).on('click', '.collapsable .toggle', function() {
            $(this).closest('.collapsable').toggleClass('expanded');
        });

        //Swipeable lists
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
    });
})(jQuery)
