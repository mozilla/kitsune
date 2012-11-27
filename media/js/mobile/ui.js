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

        $(document).on('click', '.select-box', function() {
            var overlay = $(this).data('overlay');
            if (overlay) {
                $('#' + overlay).show();
            }
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
