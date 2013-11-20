(function($, BD) {
    $(function() {
        $('.download-firefox .download-button').on('click', function(ev) {
            if (BD.version == $(this).data('latest-version')) {
                ev.stopPropagation();
                $(this).siblings('.help-bubble').show();
            }
        });
    });
})(jQuery, BrowserDetect);
