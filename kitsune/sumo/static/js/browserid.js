(function($) {
    $(function() {
        var $globalForm = $('#browserid-form');
        var $form = $globalForm;
        var email = $globalForm.data('email');
        if (email === '') {
            email = null;
        }

        function submitAssertion(assertion) {
            if (assertion) {
                var $next = $form.find('input[name="next"]');
                var next = $next.val();
                var $assertion = $form.find('input[name="assertion"]');

                // If there is no next set yet, make it the current URL.
                if (!next) {
                    $next.val(document.location.pathname + document.location.search);
                }

                $assertion.val(assertion.toString());

                $form.submit();
            }
        }

        $(document).on('click', '.browserid-login', function(e) {
            var $this = $(this);
            var formId = $this.data('form');
            var next;

            e.preventDefault();

            if (formId) {
                $form = $('#' + formId);
            } else {
                $form = $globalForm;
            }

            next = $this.data('next') || document.location.pathname + document.location.search;
            $form.find('input[name="next"]').val(next);

            var originalText = $this.text();
            $this.text(gettext('Signing you in...'));

            navigator.id.request({
                returnTo: next,
                siteName: gettext('Mozilla Support'),
                onCancel: function() {
                    $this.text(originalText);
                }/*,
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
