/*
 * questions.js
 * Scripts for the questions app.
 */

// TODO: Figure out how to break out the functionality here into
// testable parts.

(function($){

    function init() {
        var $body = $('body');

        if($body.is('.new-question')) {
            initNewQuestion();
        }

        if($body.is('.questions')) {
            initTagFilterToggle();
        }

        if($body.is('.answers')) {
            // Put last search query into search box
            $('#support-search input[name=q]')
                .val(k.unquote($.cookie('last_search')));

            initHaveThisProblemTooAjax();
            initHelpfulVote();
            initCrashIdLinking();
            addReferrerAndQueryToVoteForm();
            new k.AjaxPreview($('#preview'));
        }

        Marky.createSimpleToolbar('.editor-tools', '#reply-content, #id_content', {cannedResponses: !$body.is('.new-question')});

        // product selector page reloading
        $('#product-selector select').change(function() {
            var val = $(this).val();
            var queryParams = k.getQueryParamsAsDict(document.location.toString());

            if (val === '') {
                delete queryParams['product'];
            } else {
                queryParams['product'] = val;
            }
            document.location = document.location.pathname + '?' + $.param(queryParams);
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
    // TODO: Stop duplicating with AAQSystemInfo.isDesktopFF.
    function isDesktopFF() {
        return document.location.pathname.indexOf('desktop') >= 0;
    }

    /*
     * Ajaxify the "I have this problem too" form
     */
    function initHaveThisProblemTooAjax() {
        var $container = $('#question div.me-too, .question-tools div.me-too');
        initAjaxForm($container, 'form', '#vote-thanks');
        $container.find('input').click(function() {
            $(this).attr('disabled', 'disabled');
        });
        $container.delegate('.kbox-close, .kbox-cancel', 'click', function(ev){
            ev.preventDefault();
            $container.unbind().remove();
        });
    }

    function addReferrerAndQueryToVoteForm() {
        // Add the source/referrer and query terms to the helpful vote form
        var urlParams = k.getQueryParamsAsDict(),
            referrer = k.getReferrer(urlParams),
            query = k.getSearchQuery(urlParams, referrer);
        $('form.helpful, .me-too form')
            .append($('<input type="hidden" name="referrer"/>')
            .attr('value', referrer))
            .append($('<input type="hidden" name="query"/>')
            .attr('value', query));
    }

    /*
     * Ajaxify the Helpful/Not Helpful form
     */
    function initHelpfulVote() {
        $('li.answer div.side-section, .answer-tools').each(function() {
            new k.AjaxVote($(this).find('form.helpful'), {
                positionMessage: true,
                removeForm: true
            });
        });
    }

    // Helper
    function initAjaxForm($container, formSelector, boxSelector,
                          onKboxClose) {
        $container.delegate(formSelector, 'submit', function(ev){
            ev.preventDefault();
            var $form = $(this);
            var url = $form.attr('action');
            var data = $form.serialize();

            $.ajax({
                url: url,
                type: 'POST',
                data: data,
                dataType: 'json',
                success: function(response) {
                    if (response.html) {
                        if($(boxSelector).length === 0) {
                            // We don't have a modal set up yet.
                            var kbox = new KBox(response.html, {
                               container: $container,
                               preClose: onKboxClose
                            });
                            kbox.open();
                        } else {
                            $(boxSelector).html($(response.html).children());
                        }
                    } else if (response.message) {
                        var html = '<div class="msg"></div>';
                        $(boxSelector)
                            .html(html)
                            .find('.msg').text(response.message);
                    }

                    // Trigger a document event for others to listen for.
                    $(document).trigger('vote', $.extend(data, {url: url}));
                },
                error: function() {
                    var message = gettext("There was an error.");
                    alert(message);
                }
            });

            return false;
        });
    }

    function initTagFilterToggle() {
        $('#toggle-tag-filter').click(function(e) {
            e.preventDefault();
            $('#tag-filter').slideToggle('fast');  // CSS3: Y U NO TRANSITION TO `height: auto;`?
            $(this).toggleClass('off');
        });
    }

    /*
     * Links all crash IDs found in the passed HTML container elements
     */
    function linkCrashIds(container) {
        if(!container) {
            return;
        }
        var crashIDRegex = new RegExp("(bp-[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})", "g");
        var crashStatsBase = "https://crash-stats.mozilla.com/report/index/";
        var helpingWithCrashesArticle = "/kb/helping-crashes";
        var iconPath = "/media/img/questions/icon.questionmark.png";
        var crashReportContainer =
            "<span class='crash-report'>" +
            "<a href='" + crashStatsBase + "$1' target='_blank'>$1</a>" +
            "<a href='" + helpingWithCrashesArticle + "' target='_blank'>" +
            "<img src='" + iconPath + "'></img></a></span>";

        container.html(
            container.html().replace(crashIDRegex,
                crashReportContainer));
    }

    // For testing purposes only:
    k.linkCrashIds = linkCrashIds;

    /*
     * Initialize the automatic linking of crash IDs
     */
    function initCrashIdLinking() {
        var postContents = $(".question .main-content, .answer .main-content, #more-system-details");
        postContents.each(function() {
            linkCrashIds($(this));
        });
    }

    $(document).ready(init);

}(jQuery));
