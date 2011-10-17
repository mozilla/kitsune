/*global Marky, document, jQuery */
/*
 * forums.js
 * Scripts for the forums app.
 */

(function($){

    function init() {
        initReportPost();
        Marky.createSimpleToolbar('.editor-tools', '#reply-content, #id_content');
        new k.AjaxPreview($('#preview'));

        $('span.post-action a.reply').click(function() {
            var post = $(this).data('post'),
                $post = $('#post-' + post),
                text = $post.find('div.content-raw').text(),
                user = $post.find('a.author-name').text(),
                reply = template("''{user} [[#post-{post}|said]]''\n<blockquote>\n{text}\n</blockquote>\n\n"),
                reply_text,
                $textarea = $('#id_content'),
                oldtext = $textarea.val();

            reply_text = reply({'user': user, 'post': post, 'text': text});

            $textarea.val(oldtext + reply_text);
            return true;
        });
    }

    /*
     * Initialize the 'Report Post' form (ajaxify) (copied from questions.js)
     */
    function initReportPost() {
        $('form.report input[type="submit"]').click(function(ev){
            ev.preventDefault();
            var $form = $(this).closest('form');
            $('div.report-post-box').remove();

            var html = '<section class="report-post-box">' +
                       '<ul class="wrap"></ul></section>';
                $html = $(html),
                $ul = $html.find('ul'),
                kbox = new KBox($html, {
                    title: gettext('Report this Article'),
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
            $ul.append('<li><input type="text" class="text" ' +
                       'name="modal-other" /></li>');

            $html.find('ul a').click(function(ev){
                ev.preventDefault();
                $form.find('select').val($(this).data('val'));
                var other = $html.find('input[name="modal-other"]').val();
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

            kbox.open();
        });
    }

    $(document).ready(init);

}(jQuery));
