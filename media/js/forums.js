/*global Marky, document, jQuery */
/*
 * forums.js
 * Scripts for the forums app.
 */

(function($){

    function init() {
        Marky.createSimpleToolbar(
            '.editor-tools',
            '#reply-content, #id_content',
            {mediaButton: true});

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
        watchDiscussion();

        $('img.lazy').lazyload();
    }
    function watchDiscussion() {
        // For a thread on the all discussions for a locale.
        $('.watch-form').click(function() {
            var form = $(this);
            $.post(form.attr('action'), form.serialize(), function() {
                form.find('a').toggleClass('yes').toggleClass('no');
                form.find('a.no').attr("title", gettext("You are not watching this thread"));
                form.find('a.yes').attr("title", gettext("You are watching this thread"));
            }).error(function() {
                // error growl
            });
            return false
        });

    }

    $(document).ready(init);

}(jQuery));
