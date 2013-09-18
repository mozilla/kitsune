(function($) {
    $(function() {
        var $form = $('#browserid-form');
        var email = $form.data('email');
        if (email === '') {
            email = null;
        }

        function submitAssertion(assertion) {
            if (assertion) {
                var $e = $form.find('input[name="assertion"]');
                $e.val(assertion.toString());
                $form.submit();
            }
        }

        $(document).on('click', '.browserid-login', function(e) {
            var $this = $(this);
            var next;

            e.preventDefault();

            next = $this.data('next') || document.location.pathname + document.location.search;
            $form.find('input[name="next"]').val(next);

            navigator.id.request({
                returnTo: next,
                siteName: gettext('Mozilla Support')/*,
                TODO: siteLogo: */
            });
        });

        $('a.sign-out').on('click', function(e) {
            e.preventDefault();
            navigator.id.logout();
        });

        navigator.id.watch({
            loggedInUser: email,
            onlogin: submitAssertion,
            onlogout: function() {
                window.location = $form.data('logout-url');
            }
        });

    });
})(jQuery);
