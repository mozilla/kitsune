/*
 * Ajaxify the Helpful/NotHelpful voting form on Document page
 */

(function($) {

"use strict";

var VOTE_BUTTONS_SEL = '#helpful-vote input[type="submit"]';

function ArticleHelpfulVote(positionMessage) {
    ArticleHelpfulVote.prototype.init.call(this, positionMessage);
}

ArticleHelpfulVote.prototype = {
    init: function(positionMessage) {
        var self = this,
            $btns = $(VOTE_BUTTONS_SEL);

        self.voted = false;
        self.positionMessage = positionMessage;

        $btns.click(function(e) {
            if (!self.voted) {
                var $btn = $(this),
                    $form = $btn.closest('form'),
                    data = {};
                $btns.attr('disabled', 'disabled');
                $form.addClass('busy');
                data[$btn.attr('name')] = $btn.val();
                $.ajax({
                    url: $btn.closest('form').attr('action'),
                    type: 'POST',
                    data: data,
                    dataType: 'json',
                    success: function(data) {
                        self.showMessage(data.message, $btn);
                        $btn.addClass('active');
                        $btns.removeAttr('disabled');
                        $form.removeClass('busy');
                        self.voted = true;
                    },
                    error: function() {
                        var msg = gettext('There was an error submitting your vote.');
                        self.showMessage(msg, $btn);
                        $btns.removeAttr('disabled');
                        $form.removeClass('busy');
                    }
               });
            }

            $(this).blur();
            e.preventDefault();
            return false;
        });
    },
    showMessage: function(message, $showAbove) {
        var self = this,
            $html = $('<div class="message-box"><p></p></div>'),
            offset = $showAbove.offset();
        $html.find('p').html(message);

        if (self.positionMessage) {
            // on desktop browsers we use absolute positioning
            $('body').append($html);
            $html.css({
                top: offset.top - $html.height() - 30,
                left: offset.left + $showAbove.width()/2 - $html.width()/2
            });
            var timer = setTimeout(fadeOut, 10000);
            $('body').one('click', fadeOut);
        } else {
            // on mobile browsers we just append to the grandfather
            $showAbove.parent().parent()
                .addClass($showAbove.val()).append($html);
        }

        function fadeOut() {
            $html.fadeOut(function(){
                $html.remove();
            });
            $('body').unbind('click', fadeOut);
            clearTimeout(timer);
        }
    }
};

window.ArticleHelpfulVote = ArticleHelpfulVote;

})(jQuery);