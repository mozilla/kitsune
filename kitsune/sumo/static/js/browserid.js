(function($) {
    $(function() {
        $(document).on('click', '.browserid-login', function(e) {
            e.preventDefault();

            var $this = $(this);

            var $form;
            if ($this.data('form')) {
                $form = $('#' + $this.data('form'));
            } else {
                $form = $('#browserid-form');
            }

            if ($this.data('next')) {
                $form.find('input[name="next"]').val($this.data('next'));
            }

            navigator.id.get(function(assertion) {
                if (assertion) {
                    var $e = $form.find('input[name="assertion"]');
                    $e.val(assertion.toString());
                    $form.submit();
                }
            });
        });
    });
})(jQuery);
