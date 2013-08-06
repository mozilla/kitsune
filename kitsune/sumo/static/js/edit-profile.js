(function($){
    $(function() {
        $(document).on('click', '#change-email', function(e) {
            e.preventDefault();
            navigator.id.get(function(assertion) {
                if (assertion) {
                    var $e = $('#browserid-form input[name="assertion"]');
                    $e.val(assertion.toString());
                    $e.parent().submit();
                }
            });
        });
    });
})(jQuery);
