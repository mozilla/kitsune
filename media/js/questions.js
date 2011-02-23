/*
 * questions.js
 * Scripts for the questions app.
 */

(function($){

    function init() {
        initSearch();

        if($('body').is('.new-question')) {
            initNewQuestion();
        }

        if($('body').is('.answers')) {
            initReportPost();
            initHaveThisProblemTooAjax();
            initEmailSubscribeAjax();
        }

        Marky.createSimpleToolbar('.editor-tools', '#reply-content, #id_content');
    }

    /*
     * Initialize the search widget
     */
    function initSearch() {
        // Setup the placeholder text
        $('#support-search input[name="q"]')
            // Setup the placeholder text
            .autoPlaceholderText()
            // Submit the form on Enter
            .keyup(function(ev) {
                if(ev.keyCode === 13 && $input.val()) {
                    $('#support-search form').submit();
                }
            });
    }

    /*
     * Initialize the new question page/form
     */
    function initNewQuestion() {
        var $questionForm = $('#question-form');
        new AAQSystemInfo($questionForm);
        initTitleEdit($questionForm);
        hideDetails($questionForm);
    }

    function isLoggedIn() {
        return $('#greeting span.user').length > 0;
    }

    // The title field become editable on click of the text or edit link
    function initTitleEdit($form) {
        $form.find('#title-val').click(function(ev){
            if($(ev.target).is('a, span')) {
                ev.preventDefault();
                var $this = $(this);
                var $hid = $this.find('input[type="hidden"]');
                var $textbox = $('<input type="text" name="' +
                               $hid.attr('name') + '" />');
                $textbox.val($hid.val());
                $this.unbind('click').replaceWith($textbox);
                $textbox.focus();
            }
        });
    }

    // Hide the browser/system details for users on FF with js enabled
    // and are submitting a question for FF on desktop.
    function hideDetails($form) {
        if($.browser.mozilla && isDesktopFF()) {
            $form.find('ol').addClass('hide-details');
            $form.find('a.show, a.hide').click(function(ev) {
                ev.preventDefault();
                $(this).closest('li')
                    .toggleClass('show')
                    .toggleClass('hide')
                    .closest('ol')
                        .toggleClass('show-details');
            });
        }

        if(!isDesktopFF()) {
            $form.find('li.system-details-info').hide();
        }
    }

    // Is the question for FF on the desktop?
    function isDesktopFF() {
        return document.location.search.indexOf('product=desktop') >= 0 ||
               document.location.search.indexOf('product=beta') >= 0;
    }

    /*
     * Initialize the 'Report Post' form (ajaxify)
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
                    title: gettext('Report this post'),
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

    /*
     * Ajaxify the "I have this problem too" form
     */
    function initHaveThisProblemTooAjax() {
        var $container = $('#question div.me-too');
        initAjaxForm($container, '#vote-thanks');
        $container.delegate('.kbox-close, .kbox-cancel', 'click', function(ev){
            ev.preventDefault();
            $container.unbind().remove();
        });
    }

    /*
     * Ajaxify email subscribe
     */
    function initEmailSubscribeAjax() {
        var $container = $('#question ul.actions li.email'),
            $link = $('#email-subscribe-link');
        if ($link.length > 0) {
            initAjaxForm($container, '#email-subscribe');
        }
    }

    // Helper
    function initAjaxForm($container, boxSelector) {
        $container.delegate('form', 'submit', function(ev){
            ev.preventDefault();
            var $form = $(this);
            $.ajax({
                url: $form.attr('action'),
                type: 'POST',
                data: $form.serialize(),
                dataType: 'json',
                success: function(data) {
                    if (data.html) {
                        if($(boxSelector).length === 0) {
                            // We don't have a modal set up yet.
                            var kbox = new KBox(data.html, {
                               container: $container
                            });
                            kbox.open();
                        } else {
                            $(boxSelector).html($(data.html).children());
                        }
                    } else if (data.message) {
                        var html = '<div class="msg"></div>';
                        $(boxSelector)
                            .html(html)
                            .find('.msg').text(data.message);
                    }
                },
                error: function() {
                    var message = gettext("There was an error.");
                    alert(message);
                }
            });

            return false;
        });
    }

    $(document).ready(init);

}(jQuery));
