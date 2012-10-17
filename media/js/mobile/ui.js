(function($) {
    $(function() {
        // Menu toggling
        $('#menu-button').on('click', function() {
            $('#page').toggleClass('exposed');
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
