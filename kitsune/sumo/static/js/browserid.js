(function($) {
    // Only run this code if browserid is enabled.
    if ($('#browserid-form').length === 0) {
        return;
    }

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
                returnTo: decodeURI(next),  // WTF? This is a workaround for https://github.com/mozilla/browserid/issues/3903
                siteName: gettext('Mozilla Support'),
                oncancel: function() {
                    $this.text(originalText);
                },
                siteLogo: 'https://support.cdn.mozilla.net/static/img/firefox-256.png'
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
                $('#sign-out').submit();
            }
        });

    });
})(jQuery);
