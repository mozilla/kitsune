/*global Marky, document, jQuery */
/*
 * forums.js
 * Scripts for the forums app.
 */

(function($){

    function init() {
        Marky.createSimpleToolbar('.editor-tools', '#reply-content, #id_content');
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

    $(document).ready(init);

}(jQuery));
