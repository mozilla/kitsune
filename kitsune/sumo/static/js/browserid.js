(function($) {
    $(function() {
        $(document).on('click', '.browserid-login', function(e) {
            e.preventDefault();
            navigator.id.getVerifiedEmail(function(assertion) {
                if (assertion) {
                    var $e = $('#browserid-form input[name="assertion"]');
                    $e.val(assertion.toString());
                    $e.parent().submit();
                }
            });
        });
    });
})(jQuery);

