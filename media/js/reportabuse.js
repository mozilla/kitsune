/*
 * Report abuse UI.
 */

(function($) {

"use strict";

k.ReportAbuse = {
    init: function(options) {
        options = $.extend({
            selector: 'form.report input[type="submit"]'
        }, options);

        // Click handler
        $(options.selector).click(function(ev){
            ev.preventDefault();
            var $form = $(this).closest('form');
            $('div.report-post-box').remove();

            // Build up the HTML for the kbox popup
            var html = '<section class="report-post-box">' +
                       '<ul class="wrap"></ul></section>',
                $html = $(html),
                $ul = $html.find('ul'),
                kbox = new KBox($html, {
                    title: $form.attr('title') || gettext('Report this post'),
                    position: 'none',
                    container: $form,
                    closeOnOutClick: true
                });
            $form.find('select option').each(function(){
                var $this = $(this),
                    $li = $('<li><a href="#"></a></li>'),
                    $a = $li.find('a');
                $a.attr('data-val', $this.attr('value')).text($this.text());
                $ul.append($li);
            });
            $ul.append('<li><input type="text" class="text other"/></li>');

            // Selection click handlers
            $html.find('ul a').click(function(ev){
                ev.preventDefault();
                $form.find('select').val($(this).data('val'));
                var other = $html.find('input.other').val();
                $form.find('input[name="other"]').val(other);
                $.ajax({
                    url: $form.attr('action'),
                    type: 'POST',
                    data: $form.serialize(),
                    dataType: 'json',
                    success: function(data) {
                        var $msg = $('<div class="msg"></div>');
                        $msg.text(data.message);
                        $html.find('ul').replaceWith($msg);
                    },
                    error: function() {
                        var message = gettext("There was an error."),
                            $msg = $('<div class="msg"></div>');
                        $msg.text(data.message);
                        $html.find('ul').replaceWith($msg);
                    }
                });

                return false;
            });

            // Hitting Enter key in the "Other" textbox should select other.
            $html.find('input.other').keypress(function(e) {
                if (e.keyCode == 13) {
                    e.preventDefault();
                    $html.find('a[data-val="other"]').click();
                }
            });

            kbox.open();
        });
    }
};

$(document).ready(k.ReportAbuse.init);

})(jQuery);