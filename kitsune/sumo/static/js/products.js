(function($, BD) {
    $(function() {
        $('.download-firefox .download-button').on('click', function() {
            if (BD.version == $(this).data('latest-version')) {
                $(this).siblings('.help-bubble').show();
                return false;
            }
        });
    });
})(jQuery, BrowserDetect);
