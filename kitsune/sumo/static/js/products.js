(function($, BD) {
    $(function() {
        $('.download-firefox .download-button').on('click', function(ev) {
            var latest_version = $(this).data('latest-version');
            if ((BD.version >= latest_version) && (BD.browser == 'fx')) {
                ev.stopPropagation();
                ev.preventDefault();
                $(this).siblings('.help-bubble').show();
            }
        });
    });
})(jQuery, BrowserDetect);
