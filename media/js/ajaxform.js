(function($) {

    function AjaxForm(form, options) {
        AjaxForm.prototype.init.call(this, form, options);
    }

    AjaxForm.prototype = {
        init: function(form, options) {
            var self = this;

            var defaults = {
                bindTo: 'input[type="submit"], .btn[data-type="submit"]',
                disableButtons: true,
                errorText: 'An error occured.',
                removeForm: false
            };

            options = $.extend({}, defaults, options);
            self.options = options;

            $(options.bindTo).on('click', function(ev) {
                var $this = $(this);
                var $form = $this.closest('form');
                var $buttons = $form.find(self.options.bindTo);
                var formDataArray = $form.serializeArray();
                var data = {};

                // Collect form data (including the submit button)
                for (i = 0, l = formDataArray.length; i < l; i++) {
                    data[formDataArray[i].name] = formDataArray[i].value;
                }
                data[$this.attr('name')] = $this.val();

                // Check for required fields and validate
                if ($form.data('required')) {
                    var required = $form.data('required').split(',');
                    for (var r in required) {
                        if (!data[required[r]]) {
                            $form.addClass('invalid');
                            return false;
                        }
                    }
                }

                // Custom validation using a validate function if provided
                if (typeof self.options.validate === 'function') {
                    if (!self.options.validate(data)) {
                        $form.addClass('invalid');
                        return false;
                    }
                }

                $form.removeClass('invalid');

                if (self.options.disableButtons) {
                    $buttons.attr('disabled', 'disabled');
                }

                $.ajax({
                    url: $form.attr('action'),
                    type: 'POST',
                    data: data,
                    dataType: 'json',
                    success: function(data) {
                        if (typeof self.options.beforeComplete === 'function') {
                            self.options.beforeComplete();
                        }
                        if (data.survey) {
                            $form.after(data.survey);
                        } else {
                            $form.after($('<p></p>').html(data.message));
                        }
                        if (self.options.removeForm) {
                            $form.remove();
                        }
                        if (self.options.disableButtons) {
                            $buttons.removeAttr('disabled');
                        }
                        if (typeof self.options.afterComplete === 'function') {
                            self.options.afterComplete();
                        }
                    },
                    error: function() {
                        var msg = gettext(self.options.errorText);
                        $form.after($('<p></p>').html(msg));

                        if (self.options.disableButtons) {
                            $buttons.removeAttr('disabled');
                        }
                    }
                });

                ev.preventDefault();
                return false;
            });
        }
    };

    window.k = window.k || {};
    window.k.AjaxForm = AjaxForm;

}(jQuery));
